# PromptGuard

A prompt-injection / jailbreak detection console for LLM-integrated applications.
Paste a prompt, get a Safe / Suspicious / Blocked verdict with the reasoning
behind it — backed by a database-driven rule engine that a security analyst
can edit from the admin UI with no code deploy.

**Stack:** Python, FastAPI, Jinja2 (server-rendered UI, no separate frontend
build step), SQLite via SQLAlchemy. Ships as a single Docker container —
deployable to Railway, Render, Fly.io, or any bare VPS with Docker.

## How detection works

1. **Rule-based layer** — regex/keyword rules stored in the database (seeded
   from `app/config/rules.json` on first boot). Any rule with `action=block`
   that matches returns an immediate Blocked verdict.
2. **Heuristic scoring layer** — a 0–100 score from signals like
   instruction-override language, role-play framing, encoding patterns, and
   text entropy, weighted by values in `scoring_weights` (also
   database-driven, editable via admin API).
3. **LLM-as-judge (optional)** — for scores in the "suspicious" band, an
   optional call to an LLM API for a second opinion. Disabled by default;
   enable via `LLM_JUDGE_ENABLED=true` and an API key.

See [`security.md`](security.md) for the full threat model, OWASP mapping,
and — importantly — the current known limitations of this build.

## Local setup

```bash
git clone <this-repo>
cd promptguard
cp .env.example .env
# edit .env — at minimum set SECRET_KEY and ADMIN_PASSWORD

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

Visit `http://localhost:8000` — log in with the `ADMIN_USERNAME` /
`ADMIN_PASSWORD` you set in `.env` (a first-boot seed creates this user
automatically).

## Docker / one-command deploy

```bash
cp .env.example .env   # edit values first
docker-compose up --build
```

This runs the whole app — no separate database service needed, since
SQLite lives inside the container's named volume (`promptguard_data`),
which persists across restarts and rebuilds.

### Deploying elsewhere (Railway / Render / Fly.io / bare VPS)

The image is a standard Docker container reading all config from
environment variables, so the same image works anywhere that runs Docker:

1. Build and push the image, or point the platform at this repo (most
   support "deploy from Dockerfile").
2. Set the environment variables from `.env.example` in the platform's
   dashboard.
3. Attach a persistent volume mounted at `/app/data` — without this, the
   SQLite database resets on every redeploy.
4. Expose port `8000`.

## Editing detection rules — no code deploy required

Log in as an admin and go to **Rules** in the sidebar. Every add/edit/
delete/enable-toggle takes effect within ~15 seconds (or immediately via
the "Reload engine" button) and is recorded in the **Audit Log** page.

If you'd rather edit rules as JSON directly (e.g. to bulk-import a new
rule set), see [`app/config/README.md`](app/config/README.md) for the
schema — note this file is only used to *seed* the database on first
boot; after that, the database is the source of truth, not the file.

## Running tests

```bash
pytest app/tests -v
```

CI (`.github/workflows/ci.yml`) runs lint, type-check, config validation,
and the test suite on every push.

## Backups

SQLite has no built-in replication. Run `scripts/backup_db.py` on a
schedule (cron, systemd timer, or your platform's job scheduler) to copy
the database to timestamped backup files (last 14 kept by default):

```bash
python scripts/backup_db.py
```

## Project structure

```
app/
  main.py              FastAPI app, middleware, startup seeding
  core/                settings, security (JWT/password hashing), logging, rate limiting
  db/                  SQLAlchemy engine/session, models, first-boot seeding
  schemas/              Pydantic request/response and config-validation models
  services/            rule engine (hot-reloadable), detection pipeline, auth
  api/                 route handlers (analyze, admin, auth, pages)
  config/              rules.json / scoring_weights.json — seed data only
  templates/           Jinja2 HTML templates
  static/              CSS/JS
  tests/               pytest unit + integration tests
scripts/backup_db.py   SQLite backup helper
Dockerfile, docker-compose.yml, entrypoint.sh
security.md            threat model and OWASP LLM Top 10 mapping
```

## Honest scope note

This build implements the rule-based + heuristic + optional LLM-judge
detection layers. An earlier design pass for this project also specified
a scikit-learn ML classifier trained on labeled jailbreak/benign data as
a fourth layer — that is **not** included in this version. The
`services/detection.py` pipeline is structured so that layer can be added
later without changing the API contract; treat it as a documented next
step for the portfolio writeup rather than a current feature.
