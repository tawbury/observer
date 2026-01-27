# Run this in a terminal (outside IDE) when no other git process is using the repo.
# Purpose: commit folder-cleanup changes and create backup branch.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# Remove stale locks
if (Test-Path .git/index.lock) { Remove-Item .git/index.lock -Force }
$branchLock = ".git/refs/heads/backup/folder-cleanup-20260127.lock"
if (Test-Path $branchLock) { Remove-Item $branchLock -Force -ErrorAction SilentlyContinue }

git add -A
git status -s

git commit -m @"
chore: project folder cleanup - tests, docs, .gitignore

- .gitignore: app/*.tar.gz, app/observer runtime (config/logs/universe/symbols)
- tests: conftest.py, run_local_test path fix; session_summary -> scripts/legacy
- tests: root test_track_b_direct -> tests/integration
- tests: app/observer 9 tests -> tests/integration, unit, local
- docs: completion/history docs -> docs/archive/completion_reports
- docs: monitoring configs -> infra/monitoring; test_io/test_monitoring removed
- docs: README.md added (archive/guides); chat log -> archive
- scripts/legacy: session_summary.py
"@

git branch backup/folder-cleanup-20260127

Write-Host "Done. Backup branch: backup/folder-cleanup-20260127"
git branch -a
