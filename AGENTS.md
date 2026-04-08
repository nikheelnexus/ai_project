# AGENTS.md — Developer & AI Agent Guide

Purpose: concise, actionable instructions so AI coding agents and new developers can become productive quickly in this repository.

Quick start
- Create a venv and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

- Provide runtime secrets (PowerShell example):

```powershell
# temporary for current session
$env:OPENAI_API_KEY = 'sk-...'
# or persist for the user (PowerShell): setx OPENAI_API_KEY "sk-..."
```

High-level architecture (what matters to agents)
- `agent/` — primary place for automated "agents" and orchestration logic. Look in `agent/agents/` for individual agent implementations and templates.
- `common_script/` — shared helpers and utilities used by agents (parsing, website helpers, JSON combine utilities).
- `company_ai_project/` — UI, saved_data and persistent storage used by some pipelines; contains `saved_data/` and database code under `company_ai_project/database/`.
- `search_results/`, `processed_companies.json` — canonical output locations for scraping/parsed results.

Key developer workflows
- Install deps (see above).
- Run a local agent test (example):

```powershell
python agent/test.py
```

- If a script writes to databases it often uses files under `company_ai_project/saved_data/` — inspect that folder to find DB paths and to avoid accidental deletion.

Project-specific conventions and patterns
- Agents are organized as small, single-purpose modules under `agent/agents/` and use shared helpers from `common_script/` and top-level `agent/` helpers.
- Prompts and templates: agent code tends to embed or load structured templates (follow the files in `agent/agents/*_template*` if present). Agents normally output structured JSON — prefer machine-parseable responses.
- Data-first workflow: many tools write/read JSON files in `search_results/`, `processed_companies.json`, and DB files in `company_ai_project/saved_data/`.
- Threading / DB: code that manipulates SQLite databases often uses WAL mode and explicit timeouts. See `company_ai_project/database/company_database/link.py` for an example of PRAGMA usage and connection setup.

Integration points & external dependencies
- External APIs: OpenAI-style LLM APIs and web scraping. Keep API keys out of source: use env vars as above.
- Python deps: declared in `requirements.txt`. Use the venv created in Quick start.
- Disk-backed state: `company_ai_project/saved_data/` and `search_results/` are primary integration points where agents persist intermediate and final results.

How AI agents should operate here (practical rules)
- Use existing helper functions in `common_script/` for URL normalization, scraping and text cleaning; avoid reimplementing.
- Prefer writing outputs as JSON files placed under `search_results/` or `company_ai_project/saved_data/` and update `processed_companies.json` when summarizing results.
- Respect existing schemas: inspect a few entries in `search_results/` to match field names and types.

Adding a new agent — checklist
1. Add a new module under `agent/agents/` named for the task (e.g., `my_task_agent.py`).
2. If you need a prompt template, create `my_task_agent_template.txt` or similar and keep it next to the agent.
3. Reuse helpers from `common_script/` and existing agents rather than copying code.
4. Persist outputs to `search_results/<task>/` and register any summary in `processed_companies.json` if appropriate.
5. Test locally with `python -m agent.test` or a small runner script.

Troubleshooting & common pitfalls
- Database locked errors: SQLite in concurrent scenarios — use WAL mode, increased busy_timeout, and short transactions.
- API key/permission errors: ensure env var is set and tokens are not accidentally committed.
- Large prompt / token issues: watch token usage; there are token-tracking utilities in the codebase (search for token/tokanize files).

References (start here)
- agent/ — agents and templates
- agent/agents/ — concrete agent implementations
- common_script/ — shared helpers used across agents
- company_ai_project/saved_data/ and company_ai_project/database/ — persistent storage examples (see link.py for WAL+PRAGMA patterns)
- search_results/ and processed_companies.json — where parsed outputs live
- requirements.txt and create_requirements.py — dependency management

If you want, I can:
- expand any section with concrete file-level examples (prompt snippets, code call patterns),
- add a short example agent scaffold (template file) under `agent/agents/`.

---
Generated on: 2026-03-29

