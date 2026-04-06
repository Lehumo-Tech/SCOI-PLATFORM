from fastapi import APIRouter, HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
from typing import List

from utils.auth import get_current_user
from utils.entity_utils import create_audit_log

router = APIRouter(prefix="/assets", tags=["assets"])

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

@router.get("/trace/{person_id}")
async def trace_assets(
    person_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Trace all assets linked to a person, including those disguised under trusts or nominees"""
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID")
    
    person = await db.entities.find_one({"_id": ObjectId(person_id)})
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    assets_found = []
    
    # 1. Direct ownership
    direct_rels = await db.relationships.find({
        "from_entity_id": ObjectId(person_id),
        "relationship_type": {"$in": ["OWNS", "BENEFICIAL_OWNER_OF"]}
    }).to_list(100)
    
    for rel in direct_rels:
        asset = await db.entities.find_one({"_id": rel["to_entity_id"]})
        if asset:
            assets_found.append({
                "asset_id": str(asset["_id"]),
                "asset_name": asset["raw_name"],
                "asset_type": asset.get("metadata", {}).get("asset_type", "unknown"),
                "value": asset.get("metadata", {}).get("value"),
                "ownership_type": rel["relationship_type"],
                "confidence": rel.get("confidence", 1.0),
                "via_entity": None,
                "via_type": "direct",
                "evidence": rel.get("evidence_refs", []),
                "transfer_date": asset.get("metadata", {}).get("transfer_date")
            })
    
    # 2. Via trusts (pierce the veil)
    trust_rels = await db.relationships.find({
        "from_entity_id": ObjectId(person_id),
        "relationship_type": {"$in": ["BENEFICIAL_OWNER", "TRUSTEE"]}
    }).to_list(100)
    
    for trust_rel in trust_rels:
        trust = await db.entities.find_one({"_id": trust_rel["to_entity_id"]})
        if not trust:
            continue
        
        trust_assets = await db.relationships.find({
            "from_entity_id": trust_rel["to_entity_id"],
            "relationship_type": "OWNS"
        }).to_list(100)
        
        for asset_rel in trust_assets:
            asset = await db.entities.find_one({"_id": asset_rel["to_entity_id"]})
            if asset:
                already_found = any(a["asset_id"] == str(asset["_id"]) for a in assets_found)
                if not already_found:
                    assets_found.append({
                        "asset_id": str(asset["_id"]),
                        "asset_name": asset["raw_name"],
                        "asset_type": asset.get("metadata", {}).get("asset_type", "unknown"),
                        "value": asset.get("metadata", {}).get("value"),
                        "ownership_type": "VIA_TRUST",
                        "confidence": min(trust_rel.get("confidence", 1.0), asset_rel.get("confidence", 1.0)) * 0.9,
                        "via_entity": {
                            "id": str(trust["_id"]),
                            "name": trust["raw_name"],
                            "type": "trust"
                        },
                        "via_type": "trust",
                        "evidence": trust_rel.get("evidence_refs", []) + asset_rel.get("evidence_refs", []),
                        "transfer_date": asset.get("metadata", {}).get("transfer_date")
                    })
    
    # 3. Via related persons (nominee detection)
    related_rels = await db.relationships.find({
        "from_entity_id": ObjectId(person_id),
        "relationship_type": "RELATED_TO"
    }).to_list(100)
    
    for related_rel in related_rels:
        related_person = await db.entities.find_one({"_id": related_rel["to_entity_id"]})
        if not related_person:
            continue
        
        nominee_assets = await db.relationships.find({
            "from_entity_id": related_rel["to_entity_id"],
            "relationship_type": "OWNS"
        }).to_list(100)
        
        for asset_rel in nominee_assets:
            asset = await db.entities.find_one({"_id": asset_rel["to_entity_id"]})
            if asset:
                already_found = any(a["asset_id"] == str(asset["_id"]) for a in assets_found)
                if not already_found:
                    assets_found.append({
                        "asset_id": str(asset["_id"]),
                        "asset_name": asset["raw_name"],
                        "asset_type": asset.get("metadata", {}).get("asset_type", "unknown"),
                        "value": asset.get("metadata", {}).get("value"),
                        "ownership_type": "VIA_NOMINEE",
                        "confidence": min(related_rel.get("confidence", 1.0), asset_rel.get("confidence", 1.0)) * 0.7,
                        "via_entity": {
                            "id": str(related_person["_id"]),
                            "name": related_person["raw_name"],
                            "type": "nominee/related"
                        },
                        "via_type": "nominee",
                        "evidence": related_rel.get("evidence_refs", []) + asset_rel.get("evidence_refs", []),
                        "transfer_date": asset.get("metadata", {}).get("transfer_date")
                    })
    
    total_value = sum(a.get("value", 0) or 0 for a in assets_found)
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "asset_trace", [person_id], {"total_assets": len(assets_found)}, client_ip)
    
    return {
        "person": {
            "id": str(person["_id"]),
            "name": person["raw_name"],
            "type": person["type"]
        },
        "total_assets": len(assets_found),
        "total_estimated_value": total_value,
        "assets": sorted(assets_found, key=lambda x: x.get("confidence", 0), reverse=True),
        "disclaimer": "This analysis is based on publicly available data and pattern detection. It does not constitute legal proof of ownership. Human verification required."
    }
