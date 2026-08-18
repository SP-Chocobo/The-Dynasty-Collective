# Pulls the latest code from GitHub, installs any new/changed dependencies, and
# launches the app — run this instead of `streamlit run app.py` directly if you
# want to stay current with what's been pushed.
#
# Your own data (data/, .env) is never touched by this — it's all gitignored,
# so pulling new code never overwrites your chat history, decision log, or keys.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Pulling latest changes..." -ForegroundColor Cyan
git pull

if (-not (Test-Path ".venv")) {
    Write-Host "No virtual environment found - creating one..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
. .venv\Scripts\Activate.ps1

Write-Host "Installing/updating dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet

Write-Host "Starting the app..." -ForegroundColor Cyan
streamlit run app.py
