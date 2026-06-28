from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum

class NodeType(str, Enum):
    PHONE = "phone"
    ACCOUNT = "account"
    DEVICE = "device"
    VICTIM = "victim"

class FraudNode(BaseModel):
    id: str
    type: NodeType
    label: str
    metadata: Optional[Dict] = {}

class FraudEdge(BaseModel):
    source: str
    target: str
    relationship: str
    weight: Optional[float] = 1.0

class FraudNetworkRequest(BaseModel):
    phone_numbers: Optional[List[str]] = []
    account_ids: Optional[List[str]] = []
    device_ids: Optional[List[str]] = []
    victim_reports: Optional[List[str]] = []

class FraudCluster(BaseModel):
    cluster_id: str
    ring_name: str
    node_count: int
    victim_count: int
    estimated_damage: Optional[str]
    threat_level: str

class FraudNetworkResponse(BaseModel):
    nodes: List[FraudNode]
    edges: List[FraudEdge]
    clusters: List[FraudCluster]
    intelligence_summary: str
    recommended_actions: List[str]
    analysis_id: str
    graph_stored: bool
