"""Seed mock data for SCOI demo - SA corruption investigation patterns"""
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from utils.entity_utils import hash_identifier

async def seed_mock_data(db):
    """Seed comprehensive mock data for demo purposes"""
    
    existing = await db.entities.count_documents({})
    if existing > 0:
        return
    
    # -- PERSONS --
    persons = [
        {"raw_name": "Thabo Mokwena", "type": "person", "source": "CIPC Director Registry", "source_url": "https://eservices.cipc.co.za", "metadata": {"id_number": "hashed", "dob_year": 1975, "roles": ["Director", "Trustee"]}},
        {"raw_name": "Sipho Ndlovu", "type": "person", "source": "Government Gazette", "source_url": "https://www.gpwonline.co.za", "metadata": {"dob_year": 1982, "roles": ["Director", "Municipal Official"]}},
        {"raw_name": "Naledi Khumalo", "type": "person", "source": "CIPC Director Registry", "metadata": {"dob_year": 1990, "roles": ["Director"]}},
        {"raw_name": "Johannes van der Merwe", "type": "person", "source": "Court Records", "metadata": {"dob_year": 1968, "roles": ["Trustee", "Director"]}},
        {"raw_name": "Lerato Dlamini", "type": "person", "source": "CIPC Director Registry", "metadata": {"dob_year": 1985, "roles": ["Beneficial Owner"]}},
        {"raw_name": "Mandla Zulu", "type": "person", "source": "Government Gazette", "metadata": {"dob_year": 1970, "roles": ["Municipal Manager"]}},
        {"raw_name": "Fatima Patel", "type": "person", "source": "CIPC Director Registry", "metadata": {"dob_year": 1988, "roles": ["Director", "Trustee"]}},
    ]
    
    person_ids = []
    for p in persons:
        p["hashed_id"] = hash_identifier(p["raw_name"])
        p["first_seen"] = datetime.now(timezone.utc) - timedelta(days=365)
        p["last_seen"] = datetime.now(timezone.utc)
        result = await db.entities.insert_one(p)
        person_ids.append(result.inserted_id)
    
    # -- COMPANIES --
    companies = [
        {"raw_name": "Mbokodo Infrastructure (Pty) Ltd", "type": "company", "source": "CIPC", "metadata": {"reg_no": "2023/567890/07", "status": "active", "registered_date": "2024-01-15", "sector": "Infrastructure"}},
        {"raw_name": "Khanya Consulting Services", "type": "company", "source": "CIPC", "metadata": {"reg_no": "2024/112233/07", "status": "active", "registered_date": "2024-06-01", "sector": "Consulting"}},
        {"raw_name": "Ubuntu Water Solutions (Pty) Ltd", "type": "company", "source": "CIPC", "metadata": {"reg_no": "2024/445566/07", "status": "active", "registered_date": "2024-07-10", "sector": "Water Services"}},
        {"raw_name": "Siyakhula Construction CC", "type": "company", "source": "CIPC", "metadata": {"reg_no": "2023/998877/23", "status": "active", "registered_date": "2023-03-20", "sector": "Construction"}},
        {"raw_name": "Vukuzenzele Trading", "type": "company", "source": "CIPC", "metadata": {"reg_no": "2024/334455/07", "status": "deregistered", "registered_date": "2024-08-01", "sector": "General Trading"}},
    ]
    
    company_ids = []
    for c in companies:
        c["hashed_id"] = hash_identifier(c["raw_name"])
        c["first_seen"] = datetime.now(timezone.utc) - timedelta(days=200)
        c["last_seen"] = datetime.now(timezone.utc)
        result = await db.entities.insert_one(c)
        company_ids.append(result.inserted_id)
    
    # -- TRUSTS --
    trusts = [
        {"raw_name": "Mokwena Family Trust", "type": "trust", "source": "Master of High Court", "metadata": {"reg_date": "2024-09-01", "trustee_ids": [str(person_ids[0]), str(person_ids[4])]}},
        {"raw_name": "Ndlovu Heritage Trust", "type": "trust", "source": "Master of High Court", "metadata": {"reg_date": "2024-03-15", "trustee_ids": [str(person_ids[1])]}},
    ]
    
    trust_ids = []
    for t in trusts:
        t["hashed_id"] = hash_identifier(t["raw_name"])
        t["first_seen"] = datetime.now(timezone.utc) - timedelta(days=150)
        t["last_seen"] = datetime.now(timezone.utc)
        result = await db.entities.insert_one(t)
        trust_ids.append(result.inserted_id)
    
    # -- TENDERS --
    tenders = [
        {"raw_name": "Tender: Ekurhuleni Water Infrastructure Phase 3", "type": "tender", "source": "eTender Portal", "source_url": "https://www.etenders.gov.za", "metadata": {"ref": "EKU-WTR-2024-003", "value": 45000000, "award_date": "2024-07-15", "municipality": "Ekurhuleni"}},
        {"raw_name": "Tender: Tshwane Road Rehabilitation", "type": "tender", "source": "eTender Portal", "metadata": {"ref": "TSH-RD-2024-012", "value": 28000000, "award_date": "2024-08-20", "municipality": "Tshwane"}},
        {"raw_name": "Tender: eThekwini Consulting Services", "type": "tender", "source": "eTender Portal", "metadata": {"ref": "ETH-CON-2024-005", "value": 12000000, "award_date": "2024-09-10", "municipality": "eThekwini"}},
        {"raw_name": "Tender: Ekurhuleni Building Maintenance", "type": "tender", "source": "eTender Portal", "metadata": {"ref": "EKU-BLD-2024-007", "value": 18000000, "award_date": "2024-06-25", "municipality": "Ekurhuleni"}},
        {"raw_name": "Tender: Ekurhuleni IT Systems Upgrade", "type": "tender", "source": "eTender Portal", "metadata": {"ref": "EKU-IT-2024-009", "value": 9500000, "award_date": "2024-10-01", "municipality": "Ekurhuleni"}},
    ]
    
    tender_ids = []
    for t in tenders:
        t["hashed_id"] = hash_identifier(t["raw_name"])
        t["first_seen"] = datetime.now(timezone.utc) - timedelta(days=100)
        t["last_seen"] = datetime.now(timezone.utc)
        result = await db.entities.insert_one(t)
        tender_ids.append(result.inserted_id)
    
    # -- JUDGMENTS --
    judgments = [
        {"raw_name": "State v Mokwena & Others - Fraud", "type": "judgment", "source": "SAFLII", "source_url": "https://www.saflii.org", "metadata": {"case_no": "GP/2024/12345", "court": "Gauteng High Court", "date": "2024-11-15", "outcome": "Pending"}},
    ]
    
    judgment_ids = []
    for j in judgments:
        j["hashed_id"] = hash_identifier(j["raw_name"])
        j["first_seen"] = datetime.now(timezone.utc) - timedelta(days=30)
        j["last_seen"] = datetime.now(timezone.utc)
        result = await db.entities.insert_one(j)
        judgment_ids.append(result.inserted_id)
    
    # -- ASSETS (linked to trusts/individuals) --
    assets = [
        {"raw_name": "Property: 45 Sandton Drive, Sandton", "type": "asset", "source": "Deeds Registry", "metadata": {"asset_type": "property", "value": 8500000, "registered_owner": str(trust_ids[0]), "beneficial_owner": str(person_ids[0]), "transfer_date": "2024-09-15", "previous_owner": str(person_ids[0])}},
        {"raw_name": "Property: Farm Portion 12, Hartbeespoort", "type": "asset", "source": "Deeds Registry", "metadata": {"asset_type": "property", "value": 3200000, "registered_owner": str(trust_ids[0]), "beneficial_owner": str(person_ids[0]), "transfer_date": "2024-10-01", "previous_owner": str(person_ids[4])}},
        {"raw_name": "Vehicle: 2024 Mercedes-Benz GLE 400d", "type": "asset", "source": "eNaTIS", "metadata": {"asset_type": "vehicle", "value": 1800000, "registered_owner": str(trust_ids[1]), "beneficial_owner": str(person_ids[1]), "transfer_date": "2024-08-20"}},
        {"raw_name": "Property: Unit 12, Umhlanga Ridge", "type": "asset", "source": "Deeds Registry", "metadata": {"asset_type": "property", "value": 4200000, "registered_owner": str(person_ids[6]), "beneficial_owner": str(person_ids[1]), "transfer_date": "2024-07-05"}},
    ]
    
    asset_ids = []
    for a in assets:
        a["hashed_id"] = hash_identifier(a["raw_name"])
        a["first_seen"] = datetime.now(timezone.utc) - timedelta(days=60)
        a["last_seen"] = datetime.now(timezone.utc)
        result = await db.entities.insert_one(a)
        asset_ids.append(result.inserted_id)
    
    # -- RELATIONSHIPS --
    relationships = [
        # Thabo directs multiple companies
        {"from_entity_id": person_ids[0], "to_entity_id": company_ids[0], "relationship_type": "DIRECTS", "confidence": 0.95, "evidence_refs": ["CIPC DIR-2023-567890"], "metadata": {}},
        {"from_entity_id": person_ids[0], "to_entity_id": company_ids[2], "relationship_type": "DIRECTS", "confidence": 0.95, "evidence_refs": ["CIPC DIR-2024-445566"], "metadata": {}},
        {"from_entity_id": person_ids[0], "to_entity_id": company_ids[4], "relationship_type": "DIRECTS", "confidence": 0.90, "evidence_refs": ["CIPC DIR-2024-334455"], "metadata": {}},
        
        # Sipho directs companies and is municipal official
        {"from_entity_id": person_ids[1], "to_entity_id": company_ids[1], "relationship_type": "DIRECTS", "confidence": 0.95, "evidence_refs": ["CIPC DIR-2024-112233"], "metadata": {}},
        {"from_entity_id": person_ids[1], "to_entity_id": company_ids[3], "relationship_type": "DIRECTS", "confidence": 0.85, "evidence_refs": ["CIPC DIR-2023-998877"], "metadata": {}},
        
        # Naledi directs company
        {"from_entity_id": person_ids[2], "to_entity_id": company_ids[1], "relationship_type": "DIRECTS", "confidence": 0.95, "evidence_refs": ["CIPC DIR-2024-112233"], "metadata": {}},
        
        # Trust beneficial ownership
        {"from_entity_id": person_ids[0], "to_entity_id": trust_ids[0], "relationship_type": "BENEFICIAL_OWNER", "confidence": 0.90, "evidence_refs": ["Master HC Trust Deed"], "metadata": {}},
        {"from_entity_id": person_ids[4], "to_entity_id": trust_ids[0], "relationship_type": "TRUSTEE", "confidence": 0.95, "evidence_refs": ["Master HC Trust Deed"], "metadata": {}},
        {"from_entity_id": person_ids[1], "to_entity_id": trust_ids[1], "relationship_type": "BENEFICIAL_OWNER", "confidence": 0.90, "evidence_refs": ["Master HC Trust Deed"], "metadata": {}},
        
        # Company awarded tenders (DIRECTOR_ROTATION pattern for Thabo)
        {"from_entity_id": company_ids[0], "to_entity_id": tender_ids[0], "relationship_type": "AWARDED", "confidence": 0.99, "evidence_refs": ["eTender EKU-WTR-2024-003"], "metadata": {}},
        {"from_entity_id": company_ids[2], "to_entity_id": tender_ids[3], "relationship_type": "AWARDED", "confidence": 0.99, "evidence_refs": ["eTender EKU-BLD-2024-007"], "metadata": {}},
        {"from_entity_id": company_ids[4], "to_entity_id": tender_ids[4], "relationship_type": "AWARDED", "confidence": 0.99, "evidence_refs": ["eTender EKU-IT-2024-009"], "metadata": {}},
        {"from_entity_id": company_ids[1], "to_entity_id": tender_ids[2], "relationship_type": "AWARDED", "confidence": 0.99, "evidence_refs": ["eTender ETH-CON-2024-005"], "metadata": {}},
        {"from_entity_id": company_ids[3], "to_entity_id": tender_ids[1], "relationship_type": "AWARDED", "confidence": 0.99, "evidence_refs": ["eTender TSH-RD-2024-012"], "metadata": {}},
        
        # Related persons
        {"from_entity_id": person_ids[0], "to_entity_id": person_ids[4], "relationship_type": "RELATED_TO", "confidence": 0.85, "evidence_refs": ["Trust deed analysis"], "metadata": {"type": "family"}},
        {"from_entity_id": person_ids[1], "to_entity_id": person_ids[5], "relationship_type": "RELATED_TO", "confidence": 0.70, "evidence_refs": ["Gazette appointment records"], "metadata": {"type": "professional"}},
        
        # Person involved in judgment
        {"from_entity_id": person_ids[0], "to_entity_id": judgment_ids[0], "relationship_type": "INVOLVED_IN", "confidence": 0.95, "evidence_refs": ["SAFLII GP/2024/12345"], "metadata": {}},
        
        # Asset ownership links (trust veil piercing)
        {"from_entity_id": trust_ids[0], "to_entity_id": asset_ids[0], "relationship_type": "OWNS", "confidence": 0.99, "evidence_refs": ["Deeds Registry"], "metadata": {"registered": True}},
        {"from_entity_id": trust_ids[0], "to_entity_id": asset_ids[1], "relationship_type": "OWNS", "confidence": 0.99, "evidence_refs": ["Deeds Registry"], "metadata": {"registered": True}},
        {"from_entity_id": person_ids[0], "to_entity_id": asset_ids[0], "relationship_type": "BENEFICIAL_OWNER_OF", "confidence": 0.85, "evidence_refs": ["Trust deed analysis, CIPC cross-ref"], "metadata": {"via_entity": str(trust_ids[0]), "via_type": "trust"}},
        {"from_entity_id": person_ids[0], "to_entity_id": asset_ids[1], "relationship_type": "BENEFICIAL_OWNER_OF", "confidence": 0.80, "evidence_refs": ["Trust deed analysis"], "metadata": {"via_entity": str(trust_ids[0]), "via_type": "trust"}},
        {"from_entity_id": trust_ids[1], "to_entity_id": asset_ids[2], "relationship_type": "OWNS", "confidence": 0.99, "evidence_refs": ["eNaTIS"], "metadata": {"registered": True}},
        {"from_entity_id": person_ids[1], "to_entity_id": asset_ids[2], "relationship_type": "BENEFICIAL_OWNER_OF", "confidence": 0.80, "evidence_refs": ["Trust deed cross-ref"], "metadata": {"via_entity": str(trust_ids[1]), "via_type": "trust"}},
        {"from_entity_id": person_ids[6], "to_entity_id": asset_ids[3], "relationship_type": "OWNS", "confidence": 0.99, "evidence_refs": ["Deeds Registry"], "metadata": {"registered": True}},
        {"from_entity_id": person_ids[1], "to_entity_id": asset_ids[3], "relationship_type": "BENEFICIAL_OWNER_OF", "confidence": 0.70, "evidence_refs": ["Pattern analysis - Patel linked to Ndlovu via company"], "metadata": {"via_entity": str(person_ids[6]), "via_type": "nominee"}},
    ]
    
    for r in relationships:
        r["created_at"] = datetime.now(timezone.utc)
        await db.relationships.insert_one(r)
    
    print(f"Seeded: {len(persons)} persons, {len(companies)} companies, {len(trusts)} trusts, {len(tenders)} tenders, {len(judgments)} judgments, {len(assets)} assets, {len(relationships)} relationships")
