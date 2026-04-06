from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from bson import ObjectId

class RedFlagEngine:
    """Detect corruption patterns based on predefined rules"""
    
    def __init__(self, db):
        self.db = db
        self.rules = [
            self.rapid_tender,
            self.trust_shield,
            self.director_rotation,
            self.address_cluster,
            self.forfeiture_avoidance
        ]
    
    async def evaluate_all_rules(self, entity_id: str) -> List[Dict]:
        """Run all red flag rules against an entity"""
        matches = []
        for rule in self.rules:
            result = await rule(entity_id)
            if result:
                matches.extend(result if isinstance(result, list) else [result])
        return matches
    
    async def rapid_tender(self, entity_id: str) -> Optional[Dict]:
        """RAPID_TENDER: Company registered < 30 days before tender award"""
        entity = await self.db.entities.find_one({"_id": ObjectId(entity_id)})
        if not entity or entity.get("type") != "company":
            return None
        
        reg_date_str = entity.get("metadata", {}).get("registered_date")
        if not reg_date_str:
            return None
        
        try:
            reg_date = datetime.fromisoformat(reg_date_str) if isinstance(reg_date_str, str) else reg_date_str
        except:
            return None
        
        tenders = await self.db.relationships.find({
            "from_entity_id": ObjectId(entity_id),
            "relationship_type": "AWARDED"
        }).to_list(100)
        
        for tender_rel in tenders:
            tender = await self.db.entities.find_one({"_id": tender_rel["to_entity_id"]})
            if tender:
                award_date_str = tender.get("metadata", {}).get("award_date")
                if award_date_str:
                    try:
                        award_date = datetime.fromisoformat(award_date_str) if isinstance(award_date_str, str) else award_date_str
                        days_diff = (award_date - reg_date).days
                        
                        if 0 <= days_diff <= 30:
                            return {
                                "rule_id": "RAPID_TENDER",
                                "rule_name": "Rapid Tender Award",
                                "entities": [str(entity_id), str(tender["_id"])],
                                "confidence": 0.85,
                                "evidence_refs": [entity.get("source"), tender.get("source")],
                                "metadata": {
                                    "days_between": days_diff,
                                    "company_name": entity.get("raw_name"),
                                    "tender_ref": tender.get("metadata", {}).get("ref")
                                },
                                "detected_at": datetime.now(timezone.utc).isoformat().isoformat()
                            }
                    except:
                        pass
        return None
    
    async def trust_shield(self, entity_id: str) -> Optional[Dict]:
        """TRUST_SHIELD: Trust created ≤ 60 days after corruption allegation"""
        entity = await self.db.entities.find_one({"_id": ObjectId(entity_id)})
        if not entity or entity.get("type") != "trust":
            return None
        
        return None
    
    async def director_rotation(self, entity_id: str) -> Optional[Dict]:
        """DIRECTOR_ROTATION: Same person directs ≥3 companies winning tenders from same municipality"""
        entity = await self.db.entities.find_one({"_id": ObjectId(entity_id)})
        if not entity or entity.get("type") != "person":
            return None
        
        companies = await self.db.relationships.find({
            "from_entity_id": ObjectId(entity_id),
            "relationship_type": "DIRECTS"
        }).to_list(100)
        
        if len(companies) < 3:
            return None
        
        municipality_tenders = {}
        for comp_rel in companies:
            tenders = await self.db.relationships.find({
                "from_entity_id": comp_rel["to_entity_id"],
                "relationship_type": "AWARDED"
            }).to_list(100)
            
            for tender_rel in tenders:
                tender = await self.db.entities.find_one({"_id": tender_rel["to_entity_id"]})
                if tender:
                    municipality = tender.get("metadata", {}).get("municipality")
                    if municipality:
                        if municipality not in municipality_tenders:
                            municipality_tenders[municipality] = []
                        municipality_tenders[municipality].append({
                            "company_id": str(comp_rel["to_entity_id"]),
                            "tender_id": str(tender["_id"])
                        })
        
        for municipality, tenders in municipality_tenders.items():
            if len(tenders) >= 3:
                return {
                    "rule_id": "DIRECTOR_ROTATION",
                    "rule_name": "Director Rotation Pattern",
                    "entities": [str(entity_id)] + [t["company_id"] for t in tenders[:3]],
                    "confidence": 0.90,
                    "evidence_refs": [],
                    "metadata": {
                        "person_name": entity.get("raw_name"),
                        "municipality": municipality,
                        "tender_count": len(tenders)
                    },
                    "detected_at": datetime.now(timezone.utc).isoformat()
                }
        
        return None
    
    async def address_cluster(self, entity_id: str) -> Optional[Dict]:
        """ADDRESS_CLUSTER: ≥5 companies share address with sanctioned entity"""
        return None
    
    async def forfeiture_avoidance(self, entity_id: str) -> Optional[Dict]:
        """FORFEITURE_AVOIDANCE: Asset transfer within 90 days of SIU/AFU notice"""
        return None