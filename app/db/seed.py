import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.core.logging_config import logger
from app.db.models import User, Rule, ScoringWeight
from app.schemas.rule import SeedRulesFile


def seed_admin_user(db: Session) -> None:
    existing = db.query(User).filter(User.role == "admin").first()
    if existing:
        return
    admin = User(
        username=settings.admin_username,
        email=settings.admin_email,
        hashed_password=hash_password(settings.admin_password),
        role="admin",
    )
    db.add(admin)
    db.commit()
    logger.info(f"Seeded initial admin user '{settings.admin_username}'")


def seed_rules(db: Session) -> None:
    if db.query(Rule).count() > 0:
        return
    path = Path(settings.rules_config_path)
    if not path.exists():
        logger.warning(f"Rules config not found at {path}, skipping seed")
        return

    raw = json.loads(path.read_text())
    # Validate the whole seed file against the schema before writing anything.
    validated = SeedRulesFile(**raw)

    for r in validated.rules:
        db.add(
            Rule(
                id=r.id,
                name=r.name,
                category=r.category,
                pattern=r.pattern,
                pattern_type=r.pattern_type,
                severity=r.severity,
                action=r.action,
                enabled=r.enabled,
                description=r.description,
            )
        )
    db.commit()
    logger.info(f"Seeded {len(validated.rules)} detection rules from {path}")


def seed_scoring_weights(db: Session) -> None:
    if db.query(ScoringWeight).count() > 0:
        return
    path = Path(settings.scoring_config_path)
    if not path.exists():
        logger.warning(f"Scoring config not found at {path}, skipping seed")
        return

    raw = json.loads(path.read_text())
    for w in raw.get("weights", []):
        db.add(
            ScoringWeight(
                key=w["key"],
                value=float(w["value"]),
                description=w.get("description", ""),
            )
        )
    db.commit()
    logger.info(f"Seeded {len(raw.get('weights', []))} scoring weights")


def run_all_seeds(db: Session) -> None:
    seed_admin_user(db)
    seed_rules(db)
    seed_scoring_weights(db)
