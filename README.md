# ConceptBridge-TRACE

A private-account bilingual digital-engineering learning platform. The existing visual design, student authentication, Half Adder lesson/lab, and project planner remain in place; the Learn area now contains nine complete English/Hindi/Hinglish lessons with topic-specific quizzes and account-scoped progress.

> **Hosting status:** [Open the temporary HTTPS preview](https://8000-iqz5anvcpeovrl7flmzqr-e6595978.sg2.manus.computer/). It opens at sign-in/create-account; log in or register to view the curriculum. The preview is temporary and not a permanent production deployment. No hosting provider has been provisioned.

## Curriculum

The nine lessons are grouped by topic and difficulty:

- **Fundamentals:** Logic Gates Fundamentals; Binary Number Systems; Boolean Algebra and Simplification.
- **Combinational Logic:** Half Adder; Full Adder; Multiplexers and Demultiplexers; Encoders and Decoders.
- **Sequential Logic:** SR, JK, D and T Flip-Flops; Counters and Registers.

Each lesson supplies a short overview, three objectives, substantive localized explanation sections, worked examples, a topic-appropriate interactive demonstration, relevant truth tables, three lesson-specific questions, answer feedback, rule-based misconception cues and follow-up prompts. Lesson open/completed state and quiz attempts/scores are tied to the signed-in account. The catalog and dashboard distinguish not-started, started and completed lessons; stored progress is not pre-filled. The preserved Half Adder Lab still calculates all four input cases live.

Core equations and truth-table mappings were verified in tests. The source URLs and the scope of each verification are recorded in [`app/data/curriculum-sources.md`](app/data/curriculum-sources.md). Hindi and Hinglish are draft educational copy and need fluent technical-educator review before classroom use.

## Readable lesson layout and interactive simulators

The lesson text was narrow because a legacy `.lesson-section` CSS grid reserved its first 31-pixel track for an index marker; the new lesson markup has no marker, so body text and tables auto-placed into that tiny track. The lesson article now uses full-width section flow with `min-width: 0` and explicit wrapping/scrolling for formulas and tables. Desktop keeps the article dominant beside a smaller Notes sidebar; at tablet/mobile widths the sidebar stacks below. Circuit diagrams scroll within their own figure instead of causing page-wide overflow.

Every lesson opens an integrated simulator from its own “Open Simulator” or “Open Half Adder Lab” action. The lesson page keeps its truth/state table directly below the panel. Available controls cover AND, OR, NOT, NAND, NOR, XOR, XNOR; a three-input Full Adder; independent 4:1 MUX and 1:4 DEMUX controls; 4:2 one-hot encoder and 2:4 decoder; SR/JK/D/T next-state behavior (including invalid active-high SR S=R=1); and a four-bit modulo counter and clocked shift register. Binary conversion and Boolean identity demos remain. Labeled inline SVG schematics and live outputs accompany the controls. The shared `app/static/js/simulator-core.js` contains pure, validated logic used by both the interface and `tests/test_simulators.js`; the demos do not call paid APIs or external AI services.

## Local setup (Windows / PowerShell)

Use Python 3.12+ and VS Code. The app and tests were executed in the Sandbox on Python 3.12.3; Python 3.14.2 was not available there.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
$env:COOKIE_SECURE = "false"  # localhost HTTP only; never set false on a public HTTPS deployment
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. In production, `COOKIE_SECURE` must be `true` (the Render blueprint sets this). `DATABASE_URL` defaults to a local SQLite file, `conceptbridge_accounts.sqlite3`; set it to a PostgreSQL URL to use managed Postgres. The previous `conceptbridge.db` file is left untouched.

Run the automated checks:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app migrations scripts tests
node tests/test_simulators.js
node --check app/static/js/simulator-core.js
node --check app/static/js/simulator-ui.js
node --check app/static/js/app.js
```

## Accounts and privacy

- Register with an email and a password of at least 12 characters. Passwords are salted and hashed with Python's `hashlib.scrypt`; plaintext passwords are never stored or returned.
- Sessions use random opaque tokens; only token digests are persisted. Cookies are `HttpOnly` for the session, `Secure` in production, `SameSite=Lax`, and expire after seven days. Mutations require a CSRF token. Login failures are rate-limited per normalized account identifier.
- Backend query paths derive the owner from the live session. Lesson progress, attempts, activity, projects, and tasks are scoped to the authenticated account; guessing another account's record ID returns not found.
- No email verification or password-reset email is implemented; no SMTP service is configured. Provide a verified transactional email provider and reset flow before using this for high-stakes identity or a school-wide service. The app is an MVP, not a certified student-records system.
- Curriculum copy is not confidential, but the learning app currently requires sign-in to access its APIs. Student history and projects require authentication.

## Database, migrations, and legacy data

- SQLAlchemy supports local SQLite and managed PostgreSQL. Alembic migrations run at app startup, including the additive quiz-attempt lesson-slug migration. Existing quiz attempts receive the `half-adder` slug by default; no student records are dropped.
- Production PostgreSQL connection strings must be stored only in the hosting dashboard's protected `DATABASE_URL` environment variable. Do not commit real `.env` files or paste connection strings into code, chat, or frontend settings. `.env.example` contains only a local placeholder.
- The previous local SQLite database was inspected: it contains a single empty Half Adder lesson seed and **zero** activity, quiz attempts, projects, or tasks. It is not automatically copied to a new database. It remains in place and ignored by Git.
- If importing old records later, first register the exact destination account, then use `scripts/import_legacy_sqlite.py --source conceptbridge.db --email <registered-account>`. Review source and destination first; the importer intentionally does not combine accounts or deduplicate repeat imports.

## Proposed persistent $0/month setup

**Render Free Web Service + Neon Free PostgreSQL.** `render.yaml` configures one FastAPI service with Free compute, HTTPS, secure cookies, health checks, and no auto-deploy. The Neon Postgres URL is entered as a protected Render environment variable, never committed. The included startup migration and external Postgres ensure student data survives app redeploys/restarts; SQLite is for local/temporary-preview use only.

Provider documentation was reviewed on 2026-10-14:

- Render Free: 0.1 CPU / 512 MB RAM, 750 instance-hours per workspace/month, sleeps after 15 minutes idle and may take around a minute to wake. Its filesystem is ephemeral, so it **must not** hold durable student data. No payment is required to use Free. Do not add a payment method: Render says if no method is on file, quota overages suspend free services or builds rather than billing; if a method is added, bandwidth/build overages may be billable. Render's own Free Postgres is **not suitable**: it expires after 30 days and has no backups.
- Neon Free: permanent $0 plan, no credit card required; 1 GB per-project Postgres storage, 100 CU-hours/project/month, 5 GB network transfer/project/month, compute sleeps after five idle minutes, one manual snapshot, and six hours of point-in-time restore history (up to 1 GB of changes). It does not include scheduled snapshots. Documented Free quota behavior is to suspend compute or reject writes until quota is available or the user explicitly upgrades—not auto-upgrade or automatic overage billing.
- **₹0/month is achievable only while both stay on Free tiers, no payment method is attached, no paid add-on/service is activated, and provider terms remain as documented.** This is not a lifetime cost guarantee. Expect cold starts, quota-related downtime, and limited recovery.
- Render requires a connected source-control repository. Use a **private** GitHub repo. GitHub, Render and Neon connections are not active; no cloud account/service has been provisioned. Public production deployment is separate and remains approval-gated.

Official provider sources: [Render Free limits](https://render.com/docs/free), [Render billing FAQ](https://render.com/docs/faq), [Render first deploy](https://render.com/docs/your-first-deploy), [Neon pricing](https://neon.com/pricing), [Neon plan limits](https://neon.com/docs/introduction/pro-plan), [Neon restore](https://neon.com/docs/introduction/branch-restore).

## Backups and failure behavior

Neon's Free plan has a short six-hour point-in-time history and one manual snapshot; it does **not** provide scheduled backups. Create the included manual snapshot in Neon before a schema/data migration and run `python scripts/backup_postgres.py --output-dir <private-backup-folder>` regularly to storage you control before inviting real students (install PostgreSQL client tools first). The script reads `DATABASE_URL` from the environment, not from source or command-line arguments. Treat dumps as sensitive student data and encrypt/access-control their location. It does not schedule itself. Render sleeping/restarts/redeploys do not erase the external Neon DB; the app may briefly cold-start. If free quotas are reached, use the provider's documented limit behavior; do not assume uptime. Provider/account suspension or deletion can change availability/recovery, so keep independent backups and restore by provisioning a new Postgres DB and restoring a dump.

## Main files

- `app/data/curriculum.py`: nine localized lessons, truth tables, interactive-demo descriptors, server-side quiz keys and safe serializers.
- `app/data/curriculum-sources.md`: engineering references and validation notes.
- `app/main.py`: account endpoints, CSRF/session handling, ownership, catalogue, lesson/progress/quiz and planner APIs.
- `app/models.py`, `app/database.py`, `migrations/`: owner-scoped SQLAlchemy tables, database engine and Alembic history.
- `app/data/lesson.py`, `app/data/quiz.py`: preserved Half Adder legacy content/scoring helpers.
- `app/templates/index.html`, `app/static/`: existing brand with catalog, lesson detail and quiz-picker views.
- `app/static/js/simulator-core.js`, `simulator-ui.js`: deterministic reusable circuit logic, accessible lesson-linked panels, and inline signal-flow diagrams.
- `tests/test_simulators.js`: standalone truth/state behavior checks for gates, adders, mux/demux, encoder/decoder, flip-flops, counter, and register.
- `scripts/import_legacy_sqlite.py`: explicit account-targeted local data importer.
- `scripts/backup_postgres.py`: manual custom-format PostgreSQL dump helper; not scheduled.
- `render.yaml`: proposed Render Free service only; creates no database and holds no credentials.

## Verified checks (Sandbox)

- `python3 -m unittest discover -s tests -v`: **11 tests passed**, including nine-record completeness, three locales, three topic-specific quiz questions per lesson, sanitized pre-submit quiz payloads, rule-based scoring/feedback, gate and adder equations, Boolean identities, binary examples, sequential tables, complete modulo-16 counter transitions, registration/login/logout, CSRF, two-account isolation, private planner operations and persistence after a real FastAPI process restart.
- `python3 -m compileall -q app migrations scripts tests`: passed.
- `node tests/test_simulators.js`: **11 simulator checks passed**; JavaScript syntax checks for `simulator-core.js`, `simulator-ui.js`, and `app.js` passed.
- Headless Chromium smoke checks registered a disposable local account, opened all nine lesson routes and their simulator launch actions, and exercised gate/full-adder/MUX/DEMUX/encoder/decoder/SR/JK/D/T/counter/register controls plus the preserved Half Adder Lab. Layout was measured at 1440px (article 783px, sidebar 291px), 820px (both 565px stacked), and 390px (both 306px stacked); page scroll width matched the viewport at all three sizes and lesson text used the full article width. No uncaught browser JavaScript errors were observed.
- Earlier browser checks also verified lesson completion/progress summaries, saved lesson-specific quiz attempts, the project-template UI, HTTPS preview health, and safe removal of the disposable preview smoke account. No permanent production redeploy is claimed.
- Temporary preview health returned `ok` locally and over HTTPS. Existing preview database row counts were preserved; the isolated disposable smoke-test account/data were removed afterward. No live Neon connection, Render deployment, permanent public hostname, or production redeploy is claimed.

## Learning-content limitation

English/Hindi/Hinglish copy is draft learner material and should be reviewed by a fluent technical educator before classroom use. Quiz misconception tags are transparent possible cues, not diagnoses; lesson completion is self-marked.
