from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EntityType(str, Enum):
    PHONE = "PHONE"
    ACCOUNT = "ACCOUNT"
    DEVICE = "DEVICE"
    VICTIM = "VICTIM"
    LOCATION = "LOCATION"

class Entity(BaseModel):
    id: str
    type: EntityType
    value: str
    metadata: Dict[str, Any] = {}

class Relationship(BaseModel):
    from_id: str
    to_id: str
    rel_type: str
    weight: float = 1.0

class FraudCluster(BaseModel):
    cluster_id: int
    nodes: List[str]
    size: int
    hub_node: Optional[str]
    victim_count: int
    risk_score: float

class FraudAnalysisRequest(BaseModel):
    phones: List[str] = []
    accounts: List[str] = []
    devices: List[str] = []
    victim_statement: str = ""
    session_id: Optional[str] = None

class FraudAnalysisResponse(BaseModel):
    session_id: str
    status: str
    entities: List[Entity]
    relationships: List[Relationship]
    clusters: List[FraudCluster]
    risk_level: RiskLevel
    risk_score: float
    llm_summary: str
    graph_html: str
    pdf_available: bool
    neo4j_connected: bool
    related_threats: List[Dict]
    processing_time_ms: int
