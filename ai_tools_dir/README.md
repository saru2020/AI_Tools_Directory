```text
AI Tools Directory (Frappe)

This repository contains the plan and scaffolding for an AI tools directory built on Frappe.

Overview

- Week-long plan in implementation_plan.md
- Backend/admin via Frappe
- Growth: submissions, reviews, voting, collections
- Differentiators: stacks, comparisons, AI semantic search

Prerequisites

- macOS or Linux
- Homebrew (macOS): https://brew.sh
- Python 3.11+
- Node.js 18+ and Yarn
- Redis and MariaDB
- Git and GitHub account

Quickstart (local)

1) Install dev tooling

pipx install pre-commit || python3 -m pip install --user pre-commit
pre-commit install

2) macOS bootstrap (installs system deps and bench)

bash scripts/bootstrap_macos.sh

3) Create bench, site, and app (if not already created by the script)

bench init ai_tools_bench --frappe-branch version-15
cd ai_tools_bench
bench new-site ai-tools.localhost
bench new-app ai_tools_dir
bench --site ai-tools.localhost install-app ai_tools_dir

4) Start

bench start

Import seed CSV into Tool
-------------------------

To import the normalized CSV of tools into the `Tool` doctype:

```bash
bench --site ai-tools.localhost execute ai_tools_dir.etl.import_tools.run --kwargs '{"csv_path": "/Users/saravanan/Documents/personal/github/AI_Tools/ai_tools_bench/apps/ai_tools_dir/ai_tools_seed.csv"}'
```

This upserts by `slug` (derived from `domain`) and creates/updates records accordingly.

Backfill Categories
-------------------

Create any missing categories and relink existing tools (defaults missing to "General"):

```bash
bench --site ai-tools.localhost execute ai_tools_dir.etl.backfill_categories.run
bench clear-website-cache
```

Repo standards

- Formatting/linting via pre-commit (black, ruff, hygiene hooks)
- Editor settings via .editorconfig
- CI runs pre-commit on push/PR

Environment

Copy .env.example to .env and fill in secrets as needed. For bench-managed sites, use site_config.json for site-level secrets.

CI/CD

- GitHub Actions workflow in .github/workflows/ci.yml
- Deployment jobs will be added once infrastructure is ready

Contributing

See CONTRIBUTING.md for branching, commit message style, and PR guidelines.