from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Rule, ScoringWeight, AuditLog, User
from app.schemas.rule import RuleCreate, RuleUpdate, RuleOut, ScoringWeightOut, ScoringWeightUpdate
from app.services.auth import require_admin
from app.services.rule_engine import rule_engine
from app.core.logging_config import logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _rule_to_dict(rule: Rule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "category": rule.category,
        "pattern": rule.pattern,
        "pattern_type": rule.pattern_type,
        "severity": rule.severity,
        "action": rule.action,
        "enabled": rule.enabled,
        "description": rule.description,
    }


def _write_audit(
    db: Session,
    user: User,
    request: Request,
    action: str,
    target_type: str,
    target_id: str,
    before: dict | None,
    after: dict | None,
):
    entry = AuditLog(
        user_id=user.id,
        username=user.username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before=before,
        after=after,
        ip_address=request.client.host if request.client else None,
    )
    db.add(entry)
    db.commit()


@router.get("/rules", response_model=List[RuleOut])
def list_rules(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(Rule).order_by(Rule.created_at.desc()).all()


@router.post("/rules", response_model=RuleOut)
def create_rule(
    payload: RuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rule = Rule(**payload.model_dump(), created_by=admin.id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    _write_audit(db, admin, request, "create", "rule", rule.id, None, _rule_to_dict(rule))
    rule_engine.reload(db)
    return rule


@router.put("/rules/{rule_id}", response_model=RuleOut)
def update_rule(
    rule_id: str,
    payload: RuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    before = _rule_to_dict(rule)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    # Re-validate regex if pattern or pattern_type changed
    if "pattern" in update_data or "pattern_type" in update_data:
        import re as _re

        if rule.pattern_type == "regex":
            try:
                _re.compile(rule.pattern)
            except _re.error as e:
                raise HTTPException(status_code=400, detail=f"Invalid regex: {e}")

    db.commit()
    db.refresh(rule)
    _write_audit(db, admin, request, "update", "rule", rule.id, before, _rule_to_dict(rule))
    rule_engine.reload(db)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    before = _rule_to_dict(rule)
    db.delete(rule)
    db.commit()
    _write_audit(db, admin, request, "delete", "rule", rule_id, before, None)
    rule_engine.reload(db)
    return {"status": "deleted", "id": rule_id}


@router.post("/rules/reload")
def reload_rules(
    request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    rule_engine.reload(db)
    _write_audit(db, admin, request, "reload", "rule", "*", None, {"rules_version": rule_engine.version})
    return {"status": "reloaded", "rules_version": rule_engine.version, "active_rules": len(rule_engine.rules)}


@router.get("/scoring-weights", response_model=List[ScoringWeightOut])
def list_weights(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(ScoringWeight).all()


@router.put("/scoring-weights/{key}", response_model=ScoringWeightOut)
def update_weight(
    key: str,
    payload: ScoringWeightUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    weight = db.query(ScoringWeight).filter(ScoringWeight.key == key).first()
    if not weight:
        raise HTTPException(status_code=404, detail="Scoring weight not found")
    before = {"key": weight.key, "value": weight.value}
    weight.value = payload.value
    db.commit()
    db.refresh(weight)
    _write_audit(
        db, admin, request, "update", "scoring_weight", key, before, {"key": key, "value": weight.value}
    )
    rule_engine.reload(db)
    return weight


@router.get("/audit-log")
def get_audit_log(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    entries = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": e.id,
            "username": e.username,
            "action": e.action,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "before": e.before,
            "after": e.after,
            "ip_address": e.ip_address,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]
