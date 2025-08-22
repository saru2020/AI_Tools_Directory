#!/usr/bin/env bash
set -euo pipefail

# macOS bootstrap for local dev
# - Installs Homebrew packages
# - Starts Redis/MariaDB
# - Installs frappe-bench via pipx

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install from https://brew.sh" >&2
  exit 1
fi

brew update
brew install redis mariadb@10.6 node yarn

# Start services
brew services start redis || true
brew services start mariadb@10.6 || true

# Ensure MariaDB 10.6 is linked (non-fatal if already linked)
brew link mariadb@10.6 --force || true

# Install pipx if missing
if ! command -v pipx >/dev/null 2>&1; then
  python3 -m pip install --user pipx
  python3 -m pipx ensurepath
fi

# Install frappe-bench
if ! command -v bench >/dev/null 2>&1; then
  pipx install frappe-bench
fi

echo "\nBootstrap complete. Next steps:"
echo "1) bench init ai_tools_bench --frappe-branch version-15"
echo "2) cd ai_tools_bench && bench new-site ai-tools.localhost"
echo "3) bench new-app ai_tools_dir && bench --site ai-tools.localhost install-app ai_tools_dir"
echo "4) bench start"
