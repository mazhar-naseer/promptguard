from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text

from app.db.database import get_db
from app.db.models import AnalysisLog, Rule, AuditLog
from app.services.auth import get_current_user, require_user, require_admin
from app.services.rule_engine import rule_engine
from app.core.templates import templates
from app.core.config import settings

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
    logs = db.query(AnalysisLog).order_by(AnalysisLog.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user, "logs": logs}
    )


@router.get("/admin/rules", response_class=HTMLResponse)
def admin_rules_page(request: Request, db: Session = Depends(get_db), admin=Depends(require_admin)):
    rule_rows = db.query(Rule).order_by(Rule.created_at.desc()).all()
    # Plain dicts, not ORM objects — the template serializes each rule to
    # JSON for the edit modal, and json.dumps can't handle ORM instances.
    rules = [
        {
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "pattern": r.pattern,
            "pattern_type": r.pattern_type,
            "severity": r.severity,
            "action": r.action,
            "enabled": r.enabled,
            "description": r.description or "",
        }
        for r in rule_rows
    ]
    return templates.TemplateResponse(
        "admin_rules.html", {"request": request, "user": admin, "rules": rules}
    )


@router.get("/admin/audit", response_class=HTMLResponse)
def admin_audit_page(request: Request, db: Session = Depends(get_db), admin=Depends(require_admin)):
    entries = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return templates.TemplateResponse(
        "admin_audit.html", {"request": request, "user": admin, "entries": entries}
    )


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(sql_text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "rules_loaded": len(rule_engine.rules),
        "rules_version": rule_engine.version,
        "llm_judge_enabled": settings.llm_judge_enabled,
    }


@router.get("/metrics", response_class=PlainTextResponse)
def metrics(db: Session = Depends(get_db)):
    total = db.query(AnalysisLog).count()
    safe = db.query(AnalysisLog).filter(AnalysisLog.verdict == "safe").count()
    suspicious = db.query(AnalysisLog).filter(AnalysisLog.verdict == "suspicious").count()
    blocked = db.query(AnalysisLog).filter(AnalysisLog.verdict == "blocked").count()

    lines = [
        "# HELP promptguard_analysis_total Total prompts analyzed",
        "# TYPE promptguard_analysis_total counter",
        f"promptguard_analysis_total {total}",
        "# HELP promptguard_verdict_total Prompts analyzed by verdict",
        "# TYPE promptguard_verdict_total counter",
        f'promptguard_verdict_total{{verdict="safe"}} {safe}',
        f'promptguard_verdict_total{{verdict="suspicious"}} {suspicious}',
        f'promptguard_verdict_total{{verdict="blocked"}} {blocked}',
        "# HELP promptguard_rules_active Active detection rules loaded",
        "# TYPE promptguard_rules_active gauge",
        f"promptguard_rules_active {len(rule_engine.rules)}",
    ]
    return "\n".join(lines) + "\n"
