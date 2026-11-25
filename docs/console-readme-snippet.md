<!-- Add this section to the main README.md (e.g. just before ## Roadmap). -->

## Analyst console (React + FastAPI)

A web console for the human-in-the-loop side of the loop: analysts triage alerts,
read the AI agent's advisory ticket, and record a decision (validate / false
positive / escalate). Decisions are audited, and the **analyst↔agent agreement
rate** is tracked over time — a direct, measurable signal of how good the agent's
triage is.

- **Frontend** — React + TypeScript, Tailwind, TanStack Query, URL-synced filters, optimistic mutations, Recharts.
- **Backend** — FastAPI + psycopg3 over an operational `ops` schema (`alerts`, `tickets`, `decisions`), kept separate from the analytical gold star schema.
- **Ops** — multi-stage Docker (nginx-served SPA + `/api` proxy), wired into `docker-compose`, GitHub Actions CI (pytest + typecheck + build).

See [`console/`](console/) for the full write-up and screenshots.

---

<!-- CV bullet — fill in the real agreement figure once you've run a few rounds. -->
**CV bullet:** Built a full-stack analyst console (React/TypeScript + FastAPI/PostgreSQL)
for an AI-driven SOC, with optimistic UI, SQL-side analytics and a Dockerised,
CI-tested deployment; surfaced an analyst↔agent triage agreement rate of **__%**.
