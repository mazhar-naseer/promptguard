<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,100:16213e&height=200&section=header&text=PromptGuard&fontSize=46&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Prompt%20Injection%20%26%20Jailbreak%20Detection%20for%20LLM%20Apps&descAlignY=58&descSize=16" width="100%" />

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
<img src="https://img.shields.io/badge/Jinja2-B41717?style=for-the-badge&logo=jinja&logoColor=white" />

<br/><br/>

<i>Paste a prompt → get a <b>Safe / Suspicious / Blocked</b> verdict, with the reasoning behind it —<br/>backed by a database-driven rule engine an analyst can edit with zero code deploys.</i>

</div>

<br/>

<div align="center">

<img src="https://img.shields.io/badge/status-active-2ea44f?style=flat-square" />
<img src="https://img.shields.io/badge/OWASP-LLM_Top_10_Mapped-critical?style=flat-square" />
<img src="https://img.shields.io/badge/deploy-Docker_single_container-blue?style=flat-square" />

</div>

<br/>

<div align="center">

<h2>🛰️ Overview</h2>

</div>

PromptGuard is a self-hosted detection console that sits in front of LLM-integrated applications and screens incoming prompts for injection and jailbreak attempts. Every verdict comes with an explanation, and every detection rule lives in the database — not hardcoded in the app — so a security analyst can add, tune, or disable a rule from the admin UI and have it live in seconds.

<br/>

<div align="center">

<h2>🧠 How Detection Works</h2>

</div>

<table>
<tr>
<td width="33%" valign="top" align="center">

**🔹 Layer 1**
<br/>
**Rule-Based**

Regex/keyword rules stored in the database, seeded from `rules.json` on first boot. Any matching `action=block` rule returns an immediate **Blocked** verdict.

</td>
<td width="33%" valign="top" align="center">

**🔹 Layer 2**
<br/>
**Heuristic Scoring**

A 0–100 risk score from signals like instruction-override language, role-play framing, encoding patterns, and text entropy — weights are database-driven and editable via the admin API.

</td>
<td width="33%" valign="top" align="center">

**🔹 Layer 3**
<br/>
**LLM-as-Judge**
<br/>
<sub>(optional)</sub>

For scores in the "suspicious" band, an optional second-opinion call to an LLM API. Off by default — enable with `LLM_JUDGE_ENABLED=true` + an API key.

</td>
</tr>
</table>

<p align="center"><sub>📄 Full threat model & OWASP LLM Top 10 mapping → <a href="security.md">security.md</a></sub></p>

<br/>

<div align="center">

<h2>⚙️ Local Setup</h2>

</div>

```bash
git clone https://github.com/mazhar-naseer/promptguard.git
cd promptguard
cp .env.example .env
# edit .env — at minimum set SECRET_KEY and ADMIN_PASSWORD

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

Visit `http://localhost:8000` and log in with the `ADMIN_USERNAME` / `ADMIN_PASSWORD` set in `.env` — a first-boot seed creates this user automatically.

<br/>

<div align="center">

<h2>🐳 Docker / One-Command Deploy</h2>

</div>

```bash
cp .env.example .env   # edit values first
docker-compose up --build
```

Runs the whole app with no separate database service — SQLite lives inside the container's named volume (`promptguard_data`), which persists across restarts and rebuilds.

<br/>

**Deploying elsewhere — Railway / Render / Fly.io / bare VPS**

The image is a standard Docker container reading all config from environment variables, so the same image works anywhere Docker runs:

| Step | Action |
|---|---|
| 1️⃣ | Build & push the image, or point the platform at this repo (most support "deploy from Dockerfile") |
| 2️⃣ | Set the environment variables from `.env.example` in the platform's dashboard |
| 3️⃣ | Attach a persistent volume mounted at `/app/data` — without it, SQLite resets on every redeploy |
| 4️⃣ | Expose port `8000` |

<br/>

<div align="center">

<h2>🛠️ Editing Detection Rules — No Code Deploy Required</h2>

</div>

Log in as an admin and open **Rules** in the sidebar. Every add / edit / delete / enable-toggle takes effect within ~15 seconds (or instantly via **"Reload engine"**) and is recorded in the **Audit Log** page.

Prefer editing rules as JSON directly (e.g. bulk-importing a rule set)? See [`app/config/README.md`](app/config/README.md) for the schema — note it only *seeds* the database on first boot; after that, the database is the source of truth.

<br/>

<div align="center">

<h2>✅ Running Tests</h2>

</div>

```bash
pytest app/tests -v
```

CI (`.github/workflows/ci.yml`) runs lint, type-check, config validation, and the full test suite on every push.

<br/>

<div align="center">

<h2>💾 Backups</h2>

</div>

SQLite has no built-in replication. Run `scripts/backup_db.py` on a schedule (cron, systemd timer, or your platform's job scheduler) to copy the database to timestamped backup files (last 14 kept by default):

```bash
python scripts/backup_db.py
```

<br/>

<div align="center">

<h2>🗂️ Project Structure</h2>

</div>

```
app/
  main.py              FastAPI app, middleware, startup seeding
  core/                settings, security (JWT/password hashing), logging, rate limiting
  db/                  SQLAlchemy engine/session, models, first-boot seeding
  schemas/             Pydantic request/response and config-validation models
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

<br/>

<div align="center">

<h2>📝 Honest Scope Note</h2>

</div>

> This build implements the rule-based + heuristic + optional LLM-judge detection layers. An earlier design pass also specified a scikit-learn ML classifier trained on labeled jailbreak/benign data as a fourth layer — **that is not included in this version**. `services/detection.py` is structured so that layer can be added later without changing the API contract; treat it as a documented next step rather than a current feature.

<br/>

[![PromptGuard Demo](assets/demo-thumbnail.png)](https://drive.google.com/file/d/1e4ep3Q-xw3Dvp4nffu6t4EFblNlUATfT/view?usp=drive_link)

<br/>

<div align="center">

<h2>🤝 Contributing</h2>

</div>

Contributions are welcome — please open an issue first to discuss significant changes.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push and open a Pull Request

<br/>

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:16213e,100:1a1a2e&height=100&section=footer" width="100%" />

**PromptGuard** © 2026 · Detection Engineering Applied to LLM Applications

</div>
