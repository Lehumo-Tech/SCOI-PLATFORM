import hashlib
from rapidfuzz import fuzz, process
from phonetics import metaphone
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
from bson import ObjectId

def hash_identifier(value: str, salt: str = "scoi_2026") -> str:
    """Hash personal identifiers for POPIA compliance"""
    combined = f"{salt}{value}"
    return hashlib.sha256(combined.encode()).hexdigest()

def normalize_name(name: str) -> str:
    """Normalize entity names for matching"""
    return name.lower().strip().replace("  ", " ")

def fuzzy_match_entities(query: str, candidates: List[Dict], threshold: int = 80) -> List[Tuple[Dict, float]]:
    """Match entities using fuzzy string matching"""
    query_norm = normalize_name(query)
    results = []
    
    for candidate in candidates:
        name_norm = normalize_name(candidate.get("raw_name", ""))
        score = fuzz.ratio(query_norm, name_norm)
        
        if score >= threshold:
            results.append((candidate, score / 100.0))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def phonetic_match(name1: str, name2: str) -> bool:
    """Check if two names sound similar using Metaphone"""
    try:
        meta1 = metaphone(name1)
        meta2 = metaphone(name2)
        return meta1 == meta2
    except:
        return False

def extract_metadata_fields(entity_type: str, metadata: Dict) -> Dict:
    """Extract relevant fields based on entity type"""
    if entity_type == "person":
        return {
            "id_number": metadata.get("id_number"),
            "dob_year": metadata.get("dob_year"),
            "roles": metadata.get("roles", [])
        }
    elif entity_type == "company":
        return {
            "reg_no": metadata.get("reg_no"),
            "status": metadata.get("status"),
            "registered_date": metadata.get("registered_date"),
            "sector": metadata.get("sector")
        }
    elif entity_type == "trust":
        return {
            "reg_date": metadata.get("reg_date"),
            "trustee_ids": metadata.get("trustee_ids", [])
        }
    elif entity_type == "tender":
        return {
            "ref": metadata.get("ref"),
            "value": metadata.get("value"),
            "award_date": metadata.get("award_date"),
            "municipality": metadata.get("municipality")
        }
    elif entity_type == "judgment":
        return {
            "case_no": metadata.get("case_no"),
            "court": metadata.get("court"),
            "date": metadata.get("date"),
            "outcome": metadata.get("outcome")
        }
    return metadata

async def create_audit_log(db, user_id: str, user_email: str, action: str, entity_ids: List[str], query_params: Dict, ip_address: str):
    """Create audit log entry for compliance"""
    ip_hash = hash_identifier(ip_address)
    
    await db.audit_logs.insert_one({
        "user_id": ObjectId(user_id),
        "user_email": user_email,
        "action": action,
        "entity_ids": [ObjectId(eid) for eid in entity_ids if ObjectId.is_valid(eid)],
        "query_params": query_params,
        "ip_hash": ip_hash,
        "timestamp": datetime.now(timezone.utc)
    })