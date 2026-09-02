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

# #113 / §19.5 -- see update_and_run.sh for the reasoning, which is identical. Warns rather than
# blocks: this is somebody's own copy of their own app, and refusing to start it mid-draft is a
# worse failure than starting it with a problem they were told about.
Write-Host "Running the fast test tier (~2s)..." -ForegroundColor Cyan
$fastTier = python suite_taxonomy.py --tier fast
python -m unittest $fastTier.Split(" ") 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  !! The fast test tier FAILED on this version. The app will still start, but" -ForegroundColor Red
    Write-Host "  !! something this pull changed is broken. Run this to see what:" -ForegroundColor Red
    Write-Host "  !!     python -m unittest (python suite_taxonomy.py --tier fast).Split(' ')" -ForegroundColor Red
    Write-Host ""
}

Write-Host "Starting the app..." -ForegroundColor Cyan
streamlit run app.py
