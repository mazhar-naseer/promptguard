from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class RuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = "custom"
    pattern: str = Field(..., min_length=1)
    pattern_type: str = "regex"  # regex | keyword | phrase
    severity: str = "medium"  # low | medium | high | critical
    action: str = "flag"  # flag | block
    enabled: bool = True
    description: str = ""

    @field_validator("pattern_type")
    @classmethod
    def validate_pattern_type(cls, v):
        if v not in {"regex", "keyword", "phrase"}:
            raise ValueError("pattern_type must be regex, keyword, or phrase")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v not in {"low", "medium", "high", "critical"}:
            raise ValueError("severity must be low, medium, high, or critical")
        return v

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v not in {"flag", "block"}:
            raise ValueError("action must be flag or block")
        return v

    @field_validator("pattern")
    @classmethod
    def validate_regex_compiles(cls, v, info):
        pattern_type = info.data.get("pattern_type", "regex")
        if pattern_type == "regex":
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"invalid regex pattern: {e}")
        return v


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    pattern: Optional[str] = None
    pattern_type: Optional[str] = None
    severity: Optional[str] = None
    action: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class RuleOut(RuleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScoringWeightOut(BaseModel):
    key: str
    value: float
    description: str = ""

    class Config:
        from_attributes = True


class ScoringWeightUpdate(BaseModel):
    value: float


class SeedRule(BaseModel):
    """Schema used to validate rules.json seed file entries."""

    id: str
    name: str
    category: str
    pattern: str
    pattern_type: str
    severity: str
    action: str
    enabled: bool = True
    description: str = ""


class SeedRulesFile(BaseModel):
    version: str
    rules: List[SeedRule]
