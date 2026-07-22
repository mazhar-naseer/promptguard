import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    Float,
    Integer,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="analyst")  # analyst | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc)


class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, default="custom")
    pattern = Column(Text, nullable=False)
    pattern_type = Column(String, nullable=False, default="regex")  # regex|keyword|phrase
    severity = Column(String, nullable=False, default="medium")  # low|medium|high|critical
    action = Column(String, nullable=False, default="flag")  # flag|block
    enabled = Column(Boolean, default=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)


class ScoringWeight(Base):
    __tablename__ = "scoring_weights"

    key = Column(String, primary_key=True)
    value = Column(Float, nullable=False)
    description = Column(Text, default="")
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    input_hash = Column(String, nullable=False)
    input_preview = Column(Text, nullable=False)
    verdict = Column(String, nullable=False)  # safe|suspicious|blocked
    score = Column(Float, nullable=False)
    matched_rules = Column(JSON, default=list)
    model_confidence = Column(Float, nullable=True)
    reasoning = Column(Text, default="")
    rules_version = Column(String, default="")
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=now_utc)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False)  # create|update|delete|reload
    target_type = Column(String, nullable=False)  # rule|scoring_weight
    target_id = Column(String, nullable=True)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=now_utc)


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"

    key = Column(String, primary_key=True)  # e.g. "user:<id>" or "ip:<addr>"
    window_start = Column(DateTime, default=now_utc)
    count = Column(Integer, default=0)
