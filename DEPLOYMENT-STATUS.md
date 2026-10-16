# ConceptBridge-TRACE — hosted preview and production gate

**Status checked:** 2026-10-14. **Production site not provisioned or published.**

## Review preview

Temporary secured preview: <https://8000-iqz5anvcpeovrl7flmzqr-e6595978.sg2.manus.computer/>

This runs on an isolated sandbox SQLite file. Registration works, and account data is scoped, but do not enter real student data: this is a temporary preview, not a permanent data store. The existing visual layout remains; the sign-in gate appears before learning pages. Health/home/static JavaScript returned HTTP 200 over HTTPS, unauthenticated dashboard returned HTTP 401, and the preview CSRF cookie had `Secure` with HSTS enabled.

## Proposed permanent destination — not reserved

**Candidate:** `https://conceptbridge-trace.onrender.com`

The slug's availability has not been checked or reserved because the user requested destination approval before publication. If it is unavailable, stop and request approval for a revised exact hostname; do not silently change the destination.

## Exact proposed services

- **Render Free Web Service** for FastAPI, serving both the current interface and APIs. No separate paid frontend service. Choose Free compute, set `COOKIE_SECURE=true`, and use HTTPS.
- **Neon Free PostgreSQL** as the separate persistent managed database. Put the Neon pooler `DATABASE_URL` only in Render's protected environment-variable panel. Alembic migrations run at startup. Data remains outside the ephemeral Render filesystem, so it survives app restarts/redeployments.
- **Private GitHub source repository**; app code is not intended to be public in source control. GitHub, Render and Neon accounts are not connected yet.

## ₹0/month and payment details

- Current official docs say a Render Free deployment does not require payment; Free compute gives 0.1 CPU/512 MB and 750 instance-hours/workspace/month and sleeps after 15 minutes idle. If a payment method is absent, Render suspends free services/builds when certain monthly allowances are exhausted. **If a payment method is already attached, Render says outbound bandwidth and build-pipeline overages can be billed even if all instances are Free.** No payment method will be added here; existing account billing state still needs to be checked before provisioning.
- Neon Free is a permanent $0 tier with no card requirement. Current quota: 1 GB DB/project, 100 CU-hours/project/month, 5 GB network transfer, auto scale-to-zero after five minutes, one manual snapshot and six-hour point-in-time history. Limit exhaustion suspends compute or prevents growth writes until reset/explicit upgrade; no auto-upgrade is documented.
- No paid resource or add-on has been activated. Without a payment method and while both providers stay on Free, over-limit behavior is suspension/rejection, not paid expansion. Provider terms may change, so this is not a lifetime guarantee.
- Free hosting is not always-on: Render cold starts can take about a minute. The database is durable across app deploys, but Neon Free lacks scheduled snapshots; `scripts/backup_postgres.py` supports a manual `pg_dump` backup to owner-controlled storage. It is not scheduled. The six-hour restore window does not cover old incidents or service termination.

## Existing data and verification

The original `conceptbridge.db` is intact. Inspection showed one blank lesson seed and zero lesson activity, quiz attempts, projects, or tasks. No meaningful learning/project records currently need migration. `scripts/import_legacy_sqlite.py` is available for a deliberate user-to-account import if a non-empty legacy database is later provided.

Actual checks completed locally: 7 tests passed (registration/login/logout, scrypt, CSRF, full learning workflow, two-account isolation/IDOR, and a real app-process restart with SQLite); `compileall`; `node --check`; public preview health/home/static file and unauthenticated access check. **Not tested or claimed:** Neon/PostgreSQL live connection, provider billing/account state, production domain reservation, hosted deployment, actual managed-database redeploy test, or scheduled backups.

## Approval required before production

Confirm the candidate hostname and approve only this action: create/authorize the private GitHub repository and the Render Free + Neon Free resources, with no card added, no paid upgrades/add-ons, secrets entered only in protected provider settings, and no publication to a different host. If the proposed hostname is taken or the Render account has a saved payment method that makes automatic overage charges possible, stop for a new instruction rather than change billing settings or destination.
