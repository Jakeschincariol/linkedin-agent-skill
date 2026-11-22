# Advanced LinkedIn Growth Workspace

A local-first companion to the original eleven skills. It adds a persistent editorial queue, outreach CRM and metrics ledger without changing the existing skill prompts.

## Defaults and safety

- Weekly content target: **7 posts** (one per day); this is a planning target, not a command to publish.
- Every post starts as `draft`. `approve` only records your approval for manual publication; it does not publish.
- Outreach is a tracker only. It never scrapes LinkedIn, sends email/DMs, creates connection requests, or performs follow-ups.
- Analytics are based on metrics you manually export and import. No assumption is made that restricted LinkedIn read scopes are available.
- No LinkedIn cookies, passwords, browser automation, or API tokens are collected.

## Quick start

Requires Python 3.10+; no third-party dependencies.

```bash
python -m growth_agent.app init
python -m growth_agent.app draft "A practical ML lesson" "Your post text..." --schedule 2026-11-24T09:00:00+05:30
python -m growth_agent.app approve 1
python -m growth_agent.app contact "Recruiter name" --category recruiter --organization "Company" --location Hyderabad
python -m growth_agent.app touch 1 linkedin "Reviewed profile; prepared a personalized draft"
python -m growth_agent.app report
```

Set `LINKEDIN_AGENT_DB` to change the SQLite database path. The default is `data/linkedin_agent.db`.

## Metrics import

CSV header (all columns required):

```csv
post_ref,captured_at,impressions,reactions,comments,reposts,clicks
post-001,2026-11-24T18:00:00+05:30,1200,42,8,3,12
```

Import with `python -m growth_agent.app import-metrics metrics.csv`. Re-importing the same post and capture timestamp updates that snapshot. The report aggregates snapshots, so avoid importing repeated snapshots as if they were unique posts when interpreting totals.

## Suggested seven-day editorial cadence

| Day | Pillar | Example angle |
|---|---|---|
| Monday | Applied ML | A model evaluation mistake and how to detect it |
| Tuesday | LLM engineering | Retrieval, evaluation or reliability lesson |
| Wednesday | Build log | A concrete engineering decision from a project |
| Thursday | Data science | A causal, fraud or experimentation concept |
| Friday | Claude Code | A reusable workflow or engineering skill |
| Saturday | Technical teardown | A GitHub repo, paper or model with a critical take |
| Sunday | Reflection | What changed in your engineering approach this week |

Use the existing `/li-plan`, `/li-post`, `/li-human` and `/li-audit` skills to draft and refine. Prioritize original evidence, specific project details and a restrained technical voice over volume.

## Outreach workflow

Record only contacts you have a legitimate reason to approach and public/provided professional details. Suggested categories: recruiter, senior, peer, hiring-manager. Keep source and context notes. Log every actual interaction manually; use next-follow-up dates as reminders for your own review, not automatic sends. Honor opt-outs and do not add personal or sensitive information.

## LinkedIn integration boundary

This release intentionally does not include a publisher or scraper. LinkedIn API access is permissioned and product-specific; publishing and analytics capabilities depend on an approved app, granted scopes and current platform terms. Any future integration must be a separately reviewed adapter, use official APIs, store secrets outside the repository, and retain a human approval step immediately before each external action.

## Data and privacy

SQLite stores contact records and metrics locally. Back up and protect the database; it may contain personal professional contact information. Do not commit the database, exports, tokens or private notes.
