# Hosted setup research (verified 2026-10-14)

## Proposed zero-bill configuration

**Render Free Web Service + Neon Free PostgreSQL.** Render is appropriate for the existing FastAPI server; its free service filesystem is ephemeral, so the application's durable account/progress data must live in Neon Postgres, never in SQLite or local files. Render's free deploy tutorial says no payment is required, while Neon states that Free is a permanent $0/month plan requiring no credit card. Use only those Free plans and do not add a payment method or upgrade.

### Render Free

Official docs: https://render.com/docs/free and https://render.com/docs/faq

- Free web service: 0.1 CPU and 512 MB RAM; 750 free instance-hours per workspace/calendar month.
- Sleeps after 15 minutes without inbound traffic; next request wakes it in about one minute.
- Runtime filesystem is ephemeral: local SQLite/files are lost on restart, redeploy, or sleep.
- If there is no payment method, reaching the included outbound-bandwidth limit suspends free services for the rest of the month; exhausting build-pipeline minutes disables new builds. If a payment method is added, overage charges can apply for outbound bandwidth/build pipeline. No card should be added.
- Render Free Postgres is unsuitable for permanent storage: it expires after 30 days and has no backups.

### Neon Free

Official docs: https://neon.com/pricing and https://neon.com/docs/introduction/pro-plan

- Permanent Free plan: $0/month, no credit card required.
- 100 CU-hours/project/month; compute scales to zero after five idle minutes. 1 GB Postgres storage/project (up to 20 GB/account total), 5 GB public network transfer/project/month, maximum autoscaling 2 CU.
- Free plan allows one manual snapshot, and six hours of point-in-time history capped at 1 GB of change history. Scheduled snapshots are not included.
- When the Free CU-hour or network-transfer quota is exhausted, compute is suspended until the next monthly period or an explicit upgrade. If database storage is full, writes that increase storage fail. The documented limit behavior is restriction/suspension, not automatic upgrade or overage billing. Free plan states no card required; never upgrade/add a paid plan/card for this project without user approval.
- Database data is external to Render and persists through app restarts/redeployments. Free compute suspension is a cold start, not a data deletion. Neon history window is short, so it is not a full independent backup policy.

### Other checked option

Supabase Free is $0, with 500 MB DB, 50,000 monthly active users, 5 GB egress, but projects with low activity may be paused after seven days. A paused project can be resumed from its Dashboard for up to one year. Free projects have no downloadable database backups, so Neon is preferred for its explicit no-card permanent tier and larger storage.

## Setup blockers / user control

Render deploys from a connected Git provider. A **private GitHub repository** is the likely source so application code need not be public. GitHub, Render, and Neon integrations are currently disabled in this session; no account has yet been connected and no hosted service has been created. The user must approve those connections and any external browser sign-in. Do not enter secrets into chat; provider credentials belong in protected environment-variable settings. Without a payment method on Render and without upgrading Neon, the selected plans have no provider billing path for overages; services instead suspend or reject additional usage. The free tier is suitable for a demonstration/low-traffic MVP, not an uptime guarantee.

## Official sources

[1]: https://render.com/docs/free "Render free services and limits"
[2]: https://render.com/docs/faq "Render FAQ: billing and ephemeral storage"
[3]: https://render.com/docs/your-first-deploy "Render first deploy: no payment required"
[4]: https://neon.com/pricing "Neon pricing and free plan"
[5]: https://neon.com/docs/introduction/pro-plan "Neon plans: free quotas and limit behavior"
[6]: https://neon.com/docs/introduction/branch-restore "Neon instant restore history"
[7]: https://supabase.com/pricing "Supabase pricing and Free plan limits"
[8]: https://supabase.com/docs/guides/platform/free-project-pausing "Supabase free project pause and restore"
