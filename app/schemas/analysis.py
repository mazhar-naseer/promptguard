from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=20000)


class MatchedRule(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    action: str


class AnalyzeResponse(BaseModel):
    verdict: str  # safe | suspicious | blocked
    score: float
    matched_rules: List[MatchedRule]
    model_confidence: Optional[float] = None
    reasoning: str
    rules_version: str


class AnalysisLogOut(BaseModel):
    id: str
    input_preview: str
    verdict: str
    score: float
    matched_rules: list
    created_at: str

    class Config:
        from_attributes = True
