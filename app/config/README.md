# Rule config files

These two files **seed the database on first boot only**. After that,
the database (`rules` and `scoring_weights` tables) is the live source
of truth — edit rules through the admin UI or API, not by hand-editing
these files in a running deployment. They're documented here for anyone
bulk-importing a new rule set or reviewing what shipped by default.

## `rules.json`

```json
{
  "id": "unique-rule-id",
  "name": "Human-readable name",
  "category": "instruction_override | roleplay_jailbreak | encoding_obfuscation | system_prompt_extraction | custom",
  "pattern": "regex or keyword string",
  "pattern_type": "regex | keyword | phrase",
  "severity": "low | medium | high | critical",
  "action": "flag | block",
  "enabled": true,
  "description": "why this rule exists"
}
```

- `pattern_type: regex` — `pattern` is compiled with Python's `re` module
  (case-insensitive patterns should include `(?i)` themselves). Invalid
  regex is rejected at load time with an error, not silently ignored.
- `pattern_type: keyword` / `phrase` — `pattern` is matched as a
  case-insensitive substring.
- `action: block` — an immediate Blocked verdict, no further scoring.
- `action: flag` — contributes to the heuristic score but doesn't block
  outright on its own.

## `scoring_weights.json`

Each entry is a `key`/`value`/`description`. The two special keys
`score_review_threshold` and `score_block_threshold` control where the
heuristic score crosses from Safe → Suspicious → Blocked. All other keys
are per-signal weights added to the score when that signal fires.

## Adding a new rule via the admin UI (recommended)

1. Log in as an admin, go to **Rules**.
2. Click **New rule**, fill in the fields above.
3. Save — the rule is active within seconds, no deploy needed.
4. Check **Audit Log** to confirm the change was recorded.
