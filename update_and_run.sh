#!/usr/bin/env bash
# Pulls the latest code from GitHub, installs any new/changed dependencies, and
# launches the app — run this instead of `streamlit run app.py` directly if you
# want to stay current with what's been pushed.
#
# Your own data (data/, .env) is never touched by this — it's all gitignored,
# so pulling new code never overwrites your chat history, decision log, or keys.
set -e
cd "$(dirname "$0")"

echo "Pulling latest changes..."
git pull

if [ ! -d ".venv" ]; then
    echo "No virtual environment found - creating one..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements.txt --quiet

echo "Starting the app..."
streamlit run app.py
