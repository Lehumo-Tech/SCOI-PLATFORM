from fastapi import APIRouter, HTTPException, Request, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from utils.auth import get_current_user
from utils.entity_utils import create_audit_log

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

class WatchlistAddRequest(BaseModel):
    entity_id: str
    alert_on: List[str] = Field(default_factory=lambda: ["new_relationship", "red_flag", "new_tender", "asset_transfer"])
    notes: Optional[str] = None

class AlertDismissRequest(BaseModel):
    alert_id: str

@router.get("/")
async def get_watchlist(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get user's watchlist with latest alerts"""
    user = await get_current_user(request, db)
    
    items = await db.watchlist.find(
        {"user_id": ObjectId(user["_id"])},
        {"_id": 1, "entity_id": 1, "alert_on": 1, "notes": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(100)
    
    result = []
    for item in items:
        entity = await db.entities.find_one(
            {"_id": item["entity_id"]},
            {"_id": 1, "type": 1, "raw_name": 1, "metadata": 1, "source": 1}
        )
        
        alert_count = await db.alerts.count_documents({
            "watchlist_item_id": item["_id"],
            "dismissed": False
        })
        
        result.append({
            "id": str(item["_id"]),
            "entity_id": str(item["entity_id"]),
            "entity": {
                "id": str(entity["_id"]),
                "type": entity["type"],
                "name": entity["raw_name"],
                "source": entity.get("source", ""),
            } if entity else None,
            "alert_on": item.get("alert_on", []),
            "notes": item.get("notes", ""),
            "active_alerts": alert_count,
            "created_at": item["created_at"].isoformat()
        })
    
    return {"items": result, "total": len(result)}

@router.post("/add")
async def add_to_watchlist(
    req: WatchlistAddRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add an entity to user's watchlist"""
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(req.entity_id):
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    entity = await db.entities.find_one({"_id": ObjectId(req.entity_id)})
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    existing = await db.watchlist.find_one({
        "user_id": ObjectId(user["_id"]),
        "entity_id": ObjectId(req.entity_id)
    })
    if existing:
        raise HTTPException(status_code=400, detail="Entity already on watchlist")
    
    doc = {
        "user_id": ObjectId(user["_id"]),
        "entity_id": ObjectId(req.entity_id),
        "alert_on": req.alert_on,
        "notes": req.notes or "",
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.watchlist.insert_one(doc)
    
    # Run initial scan for this entity
    alerts = await _scan_entity_for_alerts(db, ObjectId(req.entity_id), result.inserted_id)
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "watchlist_add", [req.entity_id], {"alert_on": req.alert_on}, client_ip)
    
    return {
        "id": str(result.inserted_id),
        "entity_id": req.entity_id,
        "entity_name": entity["raw_name"],
        "alerts_generated": len(alerts),
        "message": f"Added to watchlist. {len(alerts)} initial alert(s) found."
    }

@router.delete("/{item_id}")
async def remove_from_watchlist(
    item_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Remove entity from watchlist"""
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid watchlist item ID")
    
    result = await db.watchlist.delete_one({
        "_id": ObjectId(item_id),
        "user_id": ObjectId(user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    await db.alerts.delete_many({"watchlist_item_id": ObjectId(item_id)})
    
    return {"message": "Removed from watchlist"}

@router.get("/alerts")
async def get_alerts(
    dismissed: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    request: Request = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all alerts for user's watched entities"""
    user = await get_current_user(request, db)
    
    user_watchlist_ids = []
    async for item in db.watchlist.find({"user_id": ObjectId(user["_id"])}, {"_id": 1}):
        user_watchlist_ids.append(item["_id"])
    
    if not user_watchlist_ids:
        return {"alerts": [], "total": 0}
    
    query = {
        "watchlist_item_id": {"$in": user_watchlist_ids},
        "dismissed": dismissed
    }
    
    alerts = await db.alerts.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for alert in alerts:
        entity = await db.entities.find_one(
            {"_id": alert.get("entity_id")},
            {"_id": 1, "type": 1, "raw_name": 1}
        )
        
        result.append({
            "id": str(alert["_id"]),
            "entity_id": str(alert.get("entity_id", "")),
            "entity_name": entity["raw_name"] if entity else "Unknown",
            "entity_type": entity["type"] if entity else "unknown",
            "alert_type": alert["alert_type"],
            "severity": alert.get("severity", "medium"),
            "title": alert["title"],
            "description": alert["description"],
            "evidence": alert.get("evidence", []),
            "dismissed": alert.get("dismissed", False),
            "created_at": alert["created_at"].isoformat()
        })
    
    return {"alerts": result, "total": len(result)}

@router.post("/alerts/dismiss")
async def dismiss_alert(
    req: AlertDismissRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Dismiss an alert"""
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(req.alert_id):
        raise HTTPException(status_code=400, detail="Invalid alert ID")
    
    result = await db.alerts.update_one(
        {"_id": ObjectId(req.alert_id)},
        {"$set": {"dismissed": True, "dismissed_by": user["_id"], "dismissed_at": datetime.now(timezone.utc)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert dismissed"}

@router.post("/scan")
async def scan_all_watchlist(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Manually trigger scan for all watched entities"""
    user = await get_current_user(request, db)
    
    items = await db.watchlist.find({"user_id": ObjectId(user["_id"])}).to_list(100)
    
    total_alerts = 0
    for item in items:
        alerts = await _scan_entity_for_alerts(db, item["entity_id"], item["_id"])
        total_alerts += len(alerts)
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "watchlist_scan", [], {"items_scanned": len(items)}, client_ip)
    
    return {"message": f"Scanned {len(items)} entities. {total_alerts} new alert(s) generated."}


async def _scan_entity_for_alerts(db, entity_id: ObjectId, watchlist_item_id: ObjectId) -> list:
    """Scan a single entity for alerts and create alert documents"""
    from services.red_flag_engine import RedFlagEngine
    
    alerts_created = []
    entity = await db.entities.find_one({"_id": entity_id})
    if not entity:
        return alerts_created
    
    # Check for red flags
    engine = RedFlagEngine(db)
    matches = await engine.evaluate_all_rules(str(entity_id))
    
    for match in matches:
        existing = await db.alerts.find_one({
            "watchlist_item_id": watchlist_item_id,
            "alert_type": "red_flag",
            "metadata.rule_id": match["rule_id"],
            "dismissed": False
        })
        if not existing:
            alert_doc = {
                "watchlist_item_id": watchlist_item_id,
                "entity_id": entity_id,
                "alert_type": "red_flag",
                "severity": "high" if match["confidence"] > 0.8 else "medium",
                "title": f"Red Flag: {match['rule_name']}",
                "description": f"{match['rule_name']} detected with {match['confidence']*100:.0f}% confidence",
                "evidence": match.get("evidence_refs", []),
                "metadata": {"rule_id": match["rule_id"], "confidence": match["confidence"]},
                "dismissed": False,
                "created_at": datetime.now(timezone.utc)
            }
            await db.alerts.insert_one(alert_doc)
            alerts_created.append(alert_doc)
    
    # Check for new relationships
    rel_count = await db.relationships.count_documents({
        "$or": [
            {"from_entity_id": entity_id},
            {"to_entity_id": entity_id}
        ]
    })
    
    # Check for asset transfers (for persons)
    if entity.get("type") == "person":
        asset_rels = await db.relationships.find({
            "from_entity_id": entity_id,
            "relationship_type": {"$in": ["BENEFICIAL_OWNER_OF", "OWNS"]}
        }).to_list(100)
        
        for rel in asset_rels:
            asset = await db.entities.find_one({"_id": rel["to_entity_id"]})
            if asset and asset.get("metadata", {}).get("transfer_date"):
                existing = await db.alerts.find_one({
                    "watchlist_item_id": watchlist_item_id,
                    "alert_type": "asset_transfer",
                    "metadata.asset_id": str(rel["to_entity_id"]),
                    "dismissed": False
                })
                if not existing:
                    alert_doc = {
                        "watchlist_item_id": watchlist_item_id,
                        "entity_id": entity_id,
                        "alert_type": "asset_transfer",
                        "severity": "high",
                        "title": f"Asset Link: {asset['raw_name']}",
                        "description": f"Asset '{asset['raw_name']}' linked via {rel['relationship_type']} (confidence: {rel.get('confidence', 0)*100:.0f}%)",
                        "evidence": rel.get("evidence_refs", []),
                        "metadata": {"asset_id": str(rel["to_entity_id"]), "transfer_date": asset["metadata"].get("transfer_date")},
                        "dismissed": False,
                        "created_at": datetime.now(timezone.utc)
                    }
                    await db.alerts.insert_one(alert_doc)
                    alerts_created.append(alert_doc)
    
    # Check tender awards for companies
    if entity.get("type") == "company":
        tender_rels = await db.relationships.find({
            "from_entity_id": entity_id,
            "relationship_type": "AWARDED"
        }).to_list(100)
        
        for rel in tender_rels:
            tender = await db.entities.find_one({"_id": rel["to_entity_id"]})
            if tender:
                existing = await db.alerts.find_one({
                    "watchlist_item_id": watchlist_item_id,
                    "alert_type": "new_tender",
                    "metadata.tender_id": str(rel["to_entity_id"]),
                    "dismissed": False
                })
                if not existing:
                    value = tender.get("metadata", {}).get("value", 0)
                    alert_doc = {
                        "watchlist_item_id": watchlist_item_id,
                        "entity_id": entity_id,
                        "alert_type": "new_tender",
                        "severity": "high" if value and value > 10000000 else "medium",
                        "title": f"Tender Award: {tender.get('metadata', {}).get('ref', 'Unknown')}",
                        "description": f"Awarded tender '{tender['raw_name']}' worth R{value:,.0f}" if value else f"Awarded tender '{tender['raw_name']}'",
                        "evidence": rel.get("evidence_refs", []),
                        "metadata": {"tender_id": str(rel["to_entity_id"]), "value": value},
                        "dismissed": False,
                        "created_at": datetime.now(timezone.utc)
                    }
                    await db.alerts.insert_one(alert_doc)
                    alerts_created.append(alert_doc)
    
    return alerts_created
