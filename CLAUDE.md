
## Purpose
n8n workflows run unattended, and when one fails (expired credential, timeout, bad input) nobody notices until the damage is done. Flowwatch watches n8n, stores run history, shows workflow health on a dashboard, alerts on failures, and uses an LLM to explain failures in plain English.

The goal is a small, working, demoable product: trigger a failing workflow, see it appear on the dashboard, receive an alert with a readable explanation. Everything should serve that loop. Prefer the simplest design that makes it work reliably.

## How data gets in
Flowwatch gets execution data in two ways, behind one interface so the rest of the app doesn't care which was used:
- Polling (primary): a scheduled job calls the n8n REST API (executions endpoint, authenticated with an API key) and upserts runs by execution id so repeats are harmless. Needs a self-hosted n8n or a plan with API access.
- Webhook (fallback): an n8n Error Trigger workflow posts failures to Flowwatch. It gives failures only, so success-rate metrics are partial in this mode.

Define a small "collector" interface that returns normalized run records, with a polling and a webhook implementation. Normalized run record: workflow id and name, execution id, status, started and finished timestamps, duration, error message, failing node name.

## Stack
- Backend: FastAPI (Python), SQLAlchemy, Alembic, PostgreSQL
- Scheduler: APScheduler inside the backend process (no separate queue; revisit only if needed)
- Frontend: Next.js (App Router) with TypeScript, Tailwind, and Recharts
- Auth: single-tenant login with JWT in an httpOnly cookie is enough; multi-user is out of scope
- Alerts: Slack incoming webhook and Telegram bot, behind one notifier interface
- LLM: Groq, used only for failure summaries
- Infra: docker compose runs Postgres, backend, and optionally a local n8n for development and demos

## Core behaviors
1. Ingest: collectors write normalized runs to Postgres, idempotent on (instance, execution id).
2. Health: per workflow, compute success rate, run count, average duration, last failure, and a trend over a time window. Use SQL aggregates, not application loops.
3. Alerting: alert on a failure, and on repeated failures of the same workflow. Deduplicate so one outage produces one alert plus a recovery notice, not a flood. Also support a "missed run" rule for scheduled workflows that stopped running.
4. Failure summaries: send the error message, failing node name and type, and a trimmed slice of node output to the LLM. Return a short structured result (likely cause, what to check, severity). Cache by an error fingerprint so identical errors don't trigger repeated calls. Strip secrets and large payloads before anything goes to the LLM.
5. Dashboard: overview of all workflows with health status, a workflow detail page with run history and trend chart, and a failures list showing the summary and alert status for each.

## Design decisions and why
- Idempotent ingestion: polling sees the same executions many times, so upserting by execution id makes every sync safe to re-run.
- One collector interface: works for both cloud and self-hosted n8n, and makes testing easy with a fake collector.
- Alert deduplication and recovery notices: alert fatigue is what makes monitoring tools get ignored.
- LLM only where it adds value: metrics and classification are deterministic. The LLM turns messy error text into a readable explanation and nothing else.
- Credentials: the n8n API key, Groq key, and alert tokens come from environment variables. Keep .env out of git, commit a .env.example, and never print secret values in logs or output.

## Suggested build order
1. Skeleton: docker compose (Postgres, backend), FastAPI health endpoint, Next.js app, env handling.
2. Data model and polling collector against a real n8n (a local docker n8n is fine), with a seed workflow that fails on demand (webhook to an HTTP request that can return an error).
3. Health metrics endpoints and the dashboard pages.
4. Alerting with deduplication and recovery notices.
5. LLM failure summaries with fingerprint caching.
6. Auth, webhook collector, missed-run rule, README with architecture diagram and a demo script.

After each step, state how to run it and what to expect, and add a short explanation of the main design choices made in that step. Keep tests focused on the logic that can silently go wrong: idempotent ingestion, metric calculations, alert deduplication.

## Measurements
Add a small script in /scripts that produces real numbers from the running system: time from a failure occurring to the alert being delivered, ingestion time for N executions, and how many repeated failures were collapsed into single alerts. Report only numbers these scripts produce.

## Conventions
- Python with type hints, small modules, SQL migrations through Alembic.
- Keep changes scoped to what a task needs.
- Keep the README run instructions accurate as the project evolves.