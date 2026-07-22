# Security Design — PromptGuard

## Threat model

PromptGuard sits between end-user input and an LLM-integrated application.
It defends against a user (or an attacker impersonating a user) attempting to:

- Override or leak the system prompt of the downstream LLM application
- Convince the model to ignore its safety/behavioral constraints (jailbreak)
- Smuggle malicious instructions past naive keyword filters via encoding,
  role-play framing, or hypothetical wrapping

It does **not** defend against attacks on PromptGuard's own infrastructure
(that's covered by the access-control, rate-limiting, and audit-logging
controls below) or against attacks that don't touch the text input path
(e.g. attacks on the LLM's training data, or attacks via non-text modalities).

## Mapping to OWASP Top 10 for LLM Applications

| OWASP LLM risk | How PromptGuard addresses it |
|---|---|
| LLM01 Prompt Injection | Core purpose of the tool — layered rule + heuristic + LLM-judge detection before input reaches the protected application |
| LLM02 Insecure Output Handling | Out of scope for this tool (input-side only); downstream app should still sanitize LLM output |
| LLM06 Sensitive Information Disclosure | Blocked-verdict inputs are never stored in plaintext — SHA-256 hash + truncated preview only; PII scrubbing on stored previews |
| LLM07 Insecure Plugin Design | N/A — PromptGuard has no plugin system |
| LLM08 Excessive Agency | N/A — PromptGuard only classifies, it never takes autonomous action on the user's behalf |
| LLM09 Overreliance | Documented explicitly below — this tool is one layer of defense-in-depth, not a guarantee |

## Defense-in-depth, and its limits

The detection pipeline is layered deliberately: fast rule-based matching
catches known, low-effort attacks cheaply; heuristic scoring catches
variations that avoid exact keyword matches; the optional LLM-judge layer
catches attacks whose language doesn't trip either of the above.

**This is an arms race.** No layer here is claimed to be complete. Regex
rules can be evaded by novel phrasing; the heuristic scorer can be evaded
by attacks that don't spike entropy or use flagged language; the LLM
judge itself can, in principle, be prompt-injected. Treat PromptGuard as
raising the cost of a successful attack, not eliminating the risk — pair
it with least-privilege design on the downstream LLM application itself
(don't give the model capabilities it doesn't need, regardless of what
the prompt says).

## Access control

- JWT-based session auth via an httpOnly, `SameSite=Lax` cookie — never
  exposed to client-side JS, mitigating token theft via XSS
- Two roles: `analyst` (use the analyzer, view history) and `admin`
  (also manage detection rules and scoring weights)
- All role checks happen server-side in FastAPI dependencies
  (`require_user`, `require_admin`) — there is no client-side-only gate
- Admin API routes return 401/403 based on real authentication state,
  not hidden UI elements

## Data protection

- Blocked-verdict prompts are stored as a SHA-256 hash + `[redacted]`
  marker only — the tool does not become a stored archive of attack
  payloads
- Non-blocked previews are truncated to 200 characters and run through
  basic PII scrubbing (email/phone patterns) before persisting
- Secrets (JWT signing key, LLM judge API key) are read from environment
  variables only, never written to the database or committed to source

## Auditability

- Every create/update/delete on a detection rule or scoring weight
  writes an immutable row to `audit_log` (who, before/after diff, when,
  source IP)
- There is no UPDATE or DELETE code path exposed for `audit_log` records
  anywhere in the API

## Input safety

- Requests are capped at `MAX_PROMPT_LENGTH` (default 8000 characters)
  before reaching any detection logic
- Rate limiting is applied per authenticated user (or per IP for
  anonymous requests) via `slowapi`

## Known limitations (documented, not hidden)

- SQLite is a single-file database — this deployment is single-instance;
  horizontal scaling would require migrating to Postgres/MySQL
- The ML-classifier layer described in the original design doc (TF-IDF +
  logistic regression) is not yet included in this build — the current
  pipeline is rules + heuristics + optional LLM judge. Treat the ML
  layer as a documented next step, not a current claim
- The LLM-judge layer fails open (falls back to the rule/heuristic
  verdict) if the judge API is unreachable, so judge downtime does not
  take down the analyzer, but it does mean judge coverage isn't
  guaranteed during an outage
