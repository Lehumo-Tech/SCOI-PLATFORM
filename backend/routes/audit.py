from fastapi import APIRouter, Request, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime

from models.schemas import AuditLogResponse
from utils.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/audit", tags=["audit"])

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(default=100, le=500),
    skip: int = Query(default=0, ge=0),
    request: Request = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_admin(request, db)
    
    logs = await db.audit_logs.find({}, {"_id": 1, "user_id": 1, "user_email": 1, "action": 1, "entity_ids": 1, "query_params": 1, "ip_hash": 1, "timestamp": 1}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    results = []
    for log in logs:
        results.append(AuditLogResponse(
            id=str(log["_id"]),
            user_id=str(log["user_id"]),
            user_email=log["user_email"],
            action=log["action"],
            entity_ids=[str(eid) for eid in log.get("entity_ids", [])],
            query_params=log.get("query_params", {}),
            ip_hash=log["ip_hash"],
            timestamp=log["timestamp"]
        ))
    
    return results

@router.get("/export")
async def export_audit_logs(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_admin(request, db)
    
    logs = await db.audit_logs.find({}, {"_id": 0, "user_email": 1, "action": 1, "entity_ids": 1, "query_params": 1, "ip_hash": 1, "timestamp": 1}).sort("timestamp", -1).to_list(10000)
    
    return {"logs": logs, "exported_at": datetime.utcnow().isoformat(), "total": len(logs)}