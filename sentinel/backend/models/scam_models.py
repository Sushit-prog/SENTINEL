from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

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
    translated_verdict: Optional[str] = None
    translated_actions: Optional[List[str]] = None
    target_language: Optional[str] = "en"


# ── CITIZEN ALERT MODEL ──────────────────────────────────────────────────────

class EmergencyContact(BaseModel):
    name: str
    number: str
    description: str
    url: Optional[str] = None

class MHAAlertPayload(BaseModel):
    complainant_channel: str
    scam_type: str
    urgency: str
    detected_at: str
    indicators: List[Dict[str, Any]]
    recommended_freeze_window_minutes: int

class CitizenAlert(BaseModel):
    alert_id: str
    analysis_id: str
    scam_type: str
    risk_level: str
    risk_score: float
    one_line_verdict: str
    recommended_actions: List[str]
    emergency_contacts: List[EmergencyContact]
    mha_alert_payload: MHAAlertPayload
    generated_at: str
    translated_verdict: Optional[str] = None
    translated_actions: Optional[List[str]] = None
    target_language: Optional[str] = "en"
