# Contributing

Thanks for contributing! Please follow these guidelines to keep the project healthy.

## Development setup

1. Install pre-commit and enable hooks:
   ```bash
   pipx install pre-commit || python3 -m pip install --user pre-commit
   pre-commit install
   ```
2. macOS: run `bash scripts/bootstrap_macos.sh` to install Redis/MariaDB and frappe-bench.

## Branching & PRs

- Create feature branches from `main`: `feat/<short-name>`, `fix/<short-name>`
- Keep PRs small and focused; link to the relevant checklist item in `implementation_plan.md`
- Include screenshots or short notes for UI changes

## Commit style

- Conventional commits recommended (e.g., `feat: add tool detail page`)
- Run hooks locally before pushing: `pre-commit run --all-files`

## Code style

- Python: black + ruff
- Markdown: keep lines short and semantic headings

## CI

- All PRs must pass pre-commit in GitHub Actions

## Security

- Do not commit secrets. Use `.env` locally and `site_config.json` for bench sites
