from fastapi import APIRouter, HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional

from models.schemas import (
    EntityCreate, EntityResponse, RelationshipCreate, RelationshipResponse,
    SearchQuery, RedFlagMatch, ReportCreate
)
from utils.auth import get_current_user, get_current_admin
from utils.entity_utils import (
    hash_identifier, fuzzy_match_entities, extract_metadata_fields, create_audit_log
)
from services.llm_service import LLMService
from services.red_flag_engine import RedFlagEngine

router = APIRouter(prefix="/entities", tags=["entities"])

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

@router.post("/", response_model=EntityResponse, status_code=201)
async def create_entity(
    entity: EntityCreate,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_user(request, db)
    
    hashed_id = hash_identifier(entity.raw_name)
    extracted_meta = extract_metadata_fields(entity.type.value, entity.metadata)
    
    entity_doc = {
        "type": entity.type.value,
        "raw_name": entity.raw_name,
        "hashed_id": hashed_id,
        "metadata": extracted_meta,
        "source": entity.source,
        "source_url": entity.source_url,
        "first_seen": datetime.now(timezone.utc),
        "last_seen": datetime.now(timezone.utc)
    }
    
    result = await db.entities.insert_one(entity_doc)
    entity_id = str(result.inserted_id)
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "entity_create", [entity_id], entity.model_dump(), client_ip)
    
    return EntityResponse(
        id=entity_id,
        type=entity_doc["type"],
        raw_name=entity_doc["raw_name"],
        hashed_id=entity_doc["hashed_id"],
        metadata=entity_doc["metadata"],
        source=entity_doc["source"],
        source_url=entity_doc["source_url"],
        first_seen=entity_doc["first_seen"],
        last_seen=entity_doc["last_seen"]
    )

@router.post("/search", response_model=List[EntityResponse])
async def search_entities(
    query: SearchQuery,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_user(request, db)
    
    filter_query = {}
    if query.type:
        filter_query["type"] = query.type.value
    
    entities = await db.entities.find(filter_query, {"_id": 1, "type": 1, "raw_name": 1, "hashed_id": 1, "metadata": 1, "source": 1, "source_url": 1, "first_seen": 1, "last_seen": 1}).to_list(query.limit * 2)
    
    if query.fuzzy:
        matches = fuzzy_match_entities(query.query, entities, threshold=45)
        results = []
        for entity, confidence in matches[:query.limit]:
            results.append(EntityResponse(
                id=str(entity["_id"]),
                type=entity["type"],
                raw_name=entity["raw_name"],
                hashed_id=entity["hashed_id"],
                metadata=entity["metadata"],
                source=entity["source"],
                source_url=entity.get("source_url"),
                first_seen=entity["first_seen"],
                last_seen=entity["last_seen"],
                confidence_score=confidence
            ))
    else:
        results = []
        for entity in entities:
            if query.query.lower() in entity["raw_name"].lower():
                results.append(EntityResponse(
                    id=str(entity["_id"]),
                    type=entity["type"],
                    raw_name=entity["raw_name"],
                    hashed_id=entity["hashed_id"],
                    metadata=entity["metadata"],
                    source=entity["source"],
                    source_url=entity.get("source_url"),
                    first_seen=entity["first_seen"],
                    last_seen=entity["last_seen"]
                ))
            if len(results) >= query.limit:
                break
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "entity_search", [], query.model_dump(), client_ip)
    
    return results

@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(entity_id):
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    entity = await db.entities.find_one({"_id": ObjectId(entity_id)}, {"_id": 1, "type": 1, "raw_name": 1, "hashed_id": 1, "metadata": 1, "source": 1, "source_url": 1, "first_seen": 1, "last_seen": 1})
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "entity_view", [entity_id], {}, client_ip)
    
    return EntityResponse(
        id=str(entity["_id"]),
        type=entity["type"],
        raw_name=entity["raw_name"],
        hashed_id=entity["hashed_id"],
        metadata=entity["metadata"],
        source=entity["source"],
        source_url=entity.get("source_url"),
        first_seen=entity["first_seen"],
        last_seen=entity["last_seen"]
    )

@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship(
    relationship: RelationshipCreate,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(relationship.from_entity_id) or not ObjectId.is_valid(relationship.to_entity_id):
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    from_entity = await db.entities.find_one({"_id": ObjectId(relationship.from_entity_id)})
    to_entity = await db.entities.find_one({"_id": ObjectId(relationship.to_entity_id)})
    
    if not from_entity or not to_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    rel_doc = {
        "from_entity_id": ObjectId(relationship.from_entity_id),
        "to_entity_id": ObjectId(relationship.to_entity_id),
        "relationship_type": relationship.relationship_type,
        "metadata": relationship.metadata,
        "confidence": relationship.confidence,
        "evidence_refs": relationship.evidence_refs,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.relationships.insert_one(rel_doc)
    
    return RelationshipResponse(
        id=str(result.inserted_id),
        from_entity_id=relationship.from_entity_id,
        to_entity_id=relationship.to_entity_id,
        relationship_type=relationship.relationship_type,
        metadata=relationship.metadata,
        confidence=relationship.confidence,
        evidence_refs=relationship.evidence_refs,
        created_at=rel_doc["created_at"]
    )

@router.get("/graph/{entity_id}")
async def get_entity_graph(
    entity_id: str,
    hops: int = 2,
    request: Request = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(entity_id):
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    visited_entities = set()
    visited_relationships = set()
    
    async def traverse(eid: str, depth: int):
        if depth > hops or eid in visited_entities:
            return
        
        visited_entities.add(eid)
        
        outgoing = await db.relationships.find({"from_entity_id": ObjectId(eid)}).to_list(100)
        incoming = await db.relationships.find({"to_entity_id": ObjectId(eid)}).to_list(100)
        
        for rel in outgoing + incoming:
            rel_id = str(rel["_id"])
            if rel_id not in visited_relationships:
                visited_relationships.add(rel_id)
                other_id = str(rel["to_entity_id"]) if str(rel["from_entity_id"]) == eid else str(rel["from_entity_id"])
                await traverse(other_id, depth + 1)
    
    await traverse(entity_id, 0)
    
    entities = []
    for eid in visited_entities:
        entity = await db.entities.find_one({"_id": ObjectId(eid)}, {"_id": 1, "type": 1, "raw_name": 1, "metadata": 1})
        if entity:
            entities.append({
                "id": str(entity["_id"]),
                "type": entity["type"],
                "label": entity["raw_name"],
                "metadata": entity["metadata"]
            })
    
    edges = []
    for rel_id in visited_relationships:
        rel = await db.relationships.find_one({"_id": ObjectId(rel_id)})
        if rel:
            edges.append({
                "id": str(rel["_id"]),
                "source": str(rel["from_entity_id"]),
                "target": str(rel["to_entity_id"]),
                "label": rel["relationship_type"],
                "confidence": rel.get("confidence", 1.0)
            })
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "graph_view", [entity_id], {"hops": hops}, client_ip)
    
    return {"nodes": entities, "edges": edges}

@router.post("/rules/evaluate")
async def evaluate_red_flags(
    entity_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_user(request, db)
    
    if not ObjectId.is_valid(entity_id):
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    engine = RedFlagEngine(db)
    matches = await engine.evaluate_all_rules(entity_id)
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "red_flag_evaluation", [entity_id], {}, client_ip)
    
    return {"matches": matches}

@router.post("/reports/generate")
async def generate_report(
    report_request: ReportCreate,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await get_current_user(request, db)
    
    if not all(ObjectId.is_valid(eid) for eid in report_request.entity_ids):
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    main_entity = await db.entities.find_one({"_id": ObjectId(report_request.entity_ids[0])}, {"_id": 1, "type": 1, "raw_name": 1, "metadata": 1, "source": 1})
    if not main_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    relationships = []
    red_flags = []
    
    if report_request.include_graph:
        rels = await db.relationships.find({
            "$or": [
                {"from_entity_id": {"$in": [ObjectId(eid) for eid in report_request.entity_ids]}},
                {"to_entity_id": {"$in": [ObjectId(eid) for eid in report_request.entity_ids]}}
            ]
        }).to_list(100)
        
        for rel in rels:
            relationships.append({
                "from": str(rel["from_entity_id"]),
                "to": str(rel["to_entity_id"]),
                "type": rel["relationship_type"],
                "confidence": rel.get("confidence", 1.0)
            })
    
    if report_request.include_red_flags:
        engine = RedFlagEngine(db)
        for entity_id in report_request.entity_ids:
            matches = await engine.evaluate_all_rules(entity_id)
            red_flags.extend(matches)
    
    llm_service = LLMService()
    report_content = await llm_service.generate_investigation_report(
        {
            "id": str(main_entity["_id"]),
            "type": main_entity["type"],
            "raw_name": main_entity["raw_name"],
            "metadata": main_entity["metadata"],
            "source": main_entity["source"]
        },
        relationships,
        red_flags
    )
    
    report_doc = {
        "title": report_request.title,
        "entity_ids": [ObjectId(eid) for eid in report_request.entity_ids],
        "content": report_content,
        "created_by": ObjectId(user["_id"]),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.reports.insert_one(report_doc)
    
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, user["_id"], user["email"], "report_generate", report_request.entity_ids, report_request.model_dump(), client_ip)
    
    return {
        "id": str(result.inserted_id),
        "title": report_request.title,
        "content": report_content,
        "created_at": report_doc["created_at"]
    }