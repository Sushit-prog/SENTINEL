from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class AuthenticityVerdict(str, Enum):
    GENUINE = "GENUINE"
    SUSPECT = "SUSPECT"
    COUNTERFEIT = "COUNTERFEIT"
    INCONCLUSIVE = "INCONCLUSIVE"

class FeatureCheckResult(BaseModel):
    feature_name: str
    passed: bool
    confidence: float
    details: str

class CurrencyAnalysisResponse(BaseModel):
    verdict: AuthenticityVerdict
    confidence: float = Field(..., ge=0.0, le=1.0)
    denomination: Optional[str]
    feature_checks: List[FeatureCheckResult]
    ai_reasoning: str
    risk_summary: str
    analysis_id: str
    report_available: bool
