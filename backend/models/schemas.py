from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    PERSON = "person"
    COMPANY = "company"
    TRUST = "trust"
    TENDER = "tender"
    JUDGMENT = "judgment"
    ASSET = "asset"

class UserRole(str, Enum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    USER = "user"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Optional[UserRole] = UserRole.USER

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: datetime

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class EntityCreate(BaseModel):
    type: EntityType
    raw_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: str
    source_url: Optional[str] = None

class EntityResponse(BaseModel):
    id: str
    type: str
    raw_name: str
    hashed_id: str
    metadata: Dict[str, Any]
    source: str
    source_url: Optional[str]
    first_seen: datetime
    last_seen: datetime
    confidence_score: Optional[float] = None

class RelationshipCreate(BaseModel):
    from_entity_id: str
    to_entity_id: str
    relationship_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: List[str] = Field(default_factory=list)

class RelationshipResponse(BaseModel):
    id: str
    from_entity_id: str
    to_entity_id: str
    relationship_type: str
    metadata: Dict[str, Any]
    confidence: float
    evidence_refs: List[str]
    created_at: datetime

class RedFlagMatch(BaseModel):
    rule_id: str
    rule_name: str
    entities: List[str]
    confidence: float
    evidence_refs: List[str]
    metadata: Dict[str, Any]
    detected_at: datetime

class AuditLogCreate(BaseModel):
    action: str
    entity_ids: List[str] = Field(default_factory=list)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    action: str
    entity_ids: List[str]
    query_params: Dict[str, Any]
    ip_hash: str
    timestamp: datetime

class SearchQuery(BaseModel):
    query: str
    type: Optional[EntityType] = None
    fuzzy: bool = True
    limit: int = Field(default=50, le=200)

class ReportCreate(BaseModel):
    title: str
    entity_ids: List[str]
    include_graph: bool = True
    include_red_flags: bool = True