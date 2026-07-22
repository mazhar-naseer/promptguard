"""
RuleEngine is the single source of truth for detection rules and scoring
weights at runtime. Rules live in the database (seeded on first boot from
app/config/rules.json) so they can be edited via the admin UI/API without
any code change or redeploy. This module keeps a compiled, in-memory cache
that is refreshed on a short interval or on-demand via reload().
"""

import re
import threading
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from app.db.models import Rule, ScoringWeight
from app.core.logging_config import logger

CACHE_TTL_SECONDS = 15


@dataclass
class CompiledRule:
    id: str
    name: str
    category: str
    pattern_type: str
    severity: str
    action: str
    description: str
    compiled_regex: Optional[re.Pattern]
    raw_pattern: str


class RuleEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._rules: List[CompiledRule] = []
        self._weights: Dict[str, float] = {}
        self._last_loaded: float = 0.0
        self._version: str = "unloaded"

    def _compile_rule(self, rule: Rule) -> Optional[CompiledRule]:
        compiled = None
        if rule.pattern_type == "regex":
            try:
                compiled = re.compile(rule.pattern)
            except re.error as e:
                logger.error(f"Skipping rule {rule.id} — invalid regex: {e}")
                return None
        return CompiledRule(
            id=rule.id,
            name=rule.name,
            category=rule.category,
            pattern_type=rule.pattern_type,
            severity=rule.severity,
            action=rule.action,
            description=rule.description or "",
            compiled_regex=compiled,
            raw_pattern=rule.pattern,
        )

    def reload(self, db: Session) -> None:
        with self._lock:
            rules = db.query(Rule).filter(Rule.enabled == True).all()  # noqa: E712
            compiled = []
            for r in rules:
                cr = self._compile_rule(r)
                if cr:
                    compiled.append(cr)
            weights_rows = db.query(ScoringWeight).all()
            weights = {w.key: w.value for w in weights_rows}

            self._rules = compiled
            self._weights = weights
            self._last_loaded = time.time()
            self._version = str(int(self._last_loaded))
            logger.info(f"RuleEngine reloaded: {len(compiled)} active rules")

    def ensure_fresh(self, db: Session) -> None:
        if time.time() - self._last_loaded > CACHE_TTL_SECONDS:
            self.reload(db)

    @property
    def rules(self) -> List[CompiledRule]:
        return self._rules

    @property
    def weights(self) -> Dict[str, float]:
        return self._weights

    @property
    def version(self) -> str:
        return self._version

    def match(self, text: str) -> List[CompiledRule]:
        """Return all rules that match the given text."""
        matches = []
        lowered = text.lower()
        for rule in self._rules:
            if rule.pattern_type == "regex" and rule.compiled_regex:
                if rule.compiled_regex.search(text):
                    matches.append(rule)
            elif rule.pattern_type == "keyword":
                if rule.raw_pattern.lower() in lowered:
                    matches.append(rule)
            elif rule.pattern_type == "phrase":
                if rule.raw_pattern.lower() in lowered:
                    matches.append(rule)
        return matches


# Module-level singleton used across the app
rule_engine = RuleEngine()
