from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
import json
import io
import csv

from utils.auth import get_current_user
from utils.entity_utils import create_audit_log
from services.investigation_pipeline import InvestigationPipeline

router = APIRouter(prefix="/investigations", tags=["investigations"])

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

class InvestigationRequest(BaseModel):
    query: str
    entity_ids: List[str]
    title: Optional[str] = None

class ApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None

@router.post("/run")
async def run_investigation(
    req: InvestigationRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Run a full multi-agent investigation pipeline"""
    user = await get_current_user(request, db)

    if not req.entity_ids:
        raise HTTPException(status_code=400, detail="At least one entity ID required")

    for eid in req.entity_ids:
        if not ObjectId.is_valid(eid):
            raise HTTPException(status_code=400, detail=f"Invalid entity ID: {eid}")

    pipeline = InvestigationPipeline(db)
    result = await pipeline.run(req.query, req.entity_ids, user["_id"])

    # Store investigation
    inv_doc = {
        "title": req.title or f"Investigation: {req.query}",
        "query": req.query,
        "entity_ids": [ObjectId(eid) for eid in req.entity_ids],
        "result": result,
        "status": result.get("status", "complete"),
        "created_by": ObjectId(user["_id"]),
        "created_at": datetime.now(timezone.utc),
        "approved": False,
        "approved_by": None,
        "approved_at": None
    }
    insert_result = await db.investigations.insert_one(inv_doc)

    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "investigation_run", req.entity_ids, {"query": req.query}, client_ip)

    return {
        "id": str(insert_result.inserted_id),
        "title": inv_doc["title"],
        "status": result.get("status"),
        "confidence": result.get("confidence", 0),
        "compliance_score": result.get("compliance_score", 0),
        "entities_resolved": result.get("entities_resolved", 0),
        "relationships_found": result.get("relationships_found", 0),
        "red_flags_count": result.get("red_flags_count", 0),
        "report": result.get("report", ""),
        "audit_trail": result.get("audit_trail", []),
        "red_flags": result.get("red_flags", [])
    }

@router.get("/")
async def list_investigations(
    limit: int = Query(default=20, le=100),
    request: Request = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all investigations"""
    user = await get_current_user(request, db)

    investigations = await db.investigations.find(
        {"created_by": ObjectId(user["_id"])},
        {"_id": 1, "title": 1, "query": 1, "status": 1, "created_at": 1, "approved": 1,
         "result.confidence": 1, "result.compliance_score": 1, "result.red_flags_count": 1,
         "result.entities_resolved": 1}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return [{
        "id": str(inv["_id"]),
        "title": inv.get("title", ""),
        "query": inv.get("query", ""),
        "status": inv.get("status", ""),
        "approved": inv.get("approved", False),
        "confidence": inv.get("result", {}).get("confidence", 0),
        "compliance_score": inv.get("result", {}).get("compliance_score", 0),
        "red_flags_count": inv.get("result", {}).get("red_flags_count", 0),
        "entities_resolved": inv.get("result", {}).get("entities_resolved", 0),
        "created_at": inv["created_at"].isoformat()
    } for inv in investigations]

@router.get("/{investigation_id}")
async def get_investigation(
    investigation_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get full investigation details"""
    user = await get_current_user(request, db)

    if not ObjectId.is_valid(investigation_id):
        raise HTTPException(status_code=400, detail="Invalid investigation ID")

    inv = await db.investigations.find_one({"_id": ObjectId(investigation_id)})
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return {
        "id": str(inv["_id"]),
        "title": inv.get("title", ""),
        "query": inv.get("query", ""),
        "status": inv.get("status", ""),
        "approved": inv.get("approved", False),
        "result": inv.get("result", {}),
        "created_at": inv["created_at"].isoformat()
    }

@router.post("/{investigation_id}/approve")
async def approve_investigation(
    investigation_id: str,
    req: ApprovalRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Human-in-the-loop approval gate"""
    user = await get_current_user(request, db)

    if not ObjectId.is_valid(investigation_id):
        raise HTTPException(status_code=400, detail="Invalid investigation ID")

    result = await db.investigations.update_one(
        {"_id": ObjectId(investigation_id)},
        {"$set": {
            "approved": req.approved,
            "approved_by": ObjectId(user["_id"]),
            "approved_at": datetime.now(timezone.utc),
            "approval_notes": req.notes,
            "status": "approved" if req.approved else "rejected"
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Investigation not found")

    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "investigation_approval", [investigation_id], {"approved": req.approved}, client_ip)

    return {"message": f"Investigation {'approved' if req.approved else 'rejected'}"}

@router.get("/{investigation_id}/export/markdown")
async def export_markdown(
    investigation_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Export investigation report as Markdown file"""
    user = await get_current_user(request, db)

    inv = await db.investigations.find_one({"_id": ObjectId(investigation_id)})
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    report = inv.get("result", {}).get("report", "No report generated")

    return StreamingResponse(
        io.BytesIO(report.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="investigation_{investigation_id}.md"'}
    )

@router.get("/{investigation_id}/export/csv")
async def export_csv(
    investigation_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Export investigation data as CSV"""
    user = await get_current_user(request, db)

    inv = await db.investigations.find_one({"_id": ObjectId(investigation_id)})
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    result = inv.get("result", {})
    output = io.StringIO()
    writer = csv.writer(output)

    # Audit trail
    writer.writerow(["AUDIT TRAIL"])
    writer.writerow(["Timestamp", "Agent", "Action", "Detail"])
    for entry in result.get("audit_trail", []):
        writer.writerow([entry.get("timestamp"), entry.get("agent"), entry.get("action"), entry.get("detail")])

    writer.writerow([])
    writer.writerow(["RED FLAGS"])
    writer.writerow(["Rule", "Confidence", "Entities", "Details"])
    for rf in result.get("red_flags", []):
        writer.writerow([rf.get("rule_name", rf.get("rule_id")), rf.get("confidence"), len(rf.get("entities", [])), json.dumps(rf.get("metadata", {}))])

    writer.writerow([])
    writer.writerow(["RELATIONSHIPS"])
    writer.writerow(["From", "To", "Type", "Confidence", "Evidence"])
    for rel in result.get("relationships_found", []):
        if isinstance(rel, dict):
            writer.writerow([rel.get("from"), rel.get("to"), rel.get("type"), rel.get("confidence"), ", ".join(rel.get("evidence", []))])

    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="investigation_{investigation_id}.csv"'}
    )
