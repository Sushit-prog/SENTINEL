from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ScamAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Message or call transcript to analyze")
    channel: Optional[str] = Field("unknown", description="whatsapp/call/sms/email")
    language: Optional[str] = Field("en", description="Input language")

class ScamIndicator(BaseModel):
    indicator: str
    severity: RiskLevel
    explanation: str

class ScamAnalysisResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=1.0)
    scam_type: Optional[str]
    indicators: List[ScamIndicator]
    verdict: str
    recommended_action: str
    similar_patterns_found: int
    analysis_id: str
