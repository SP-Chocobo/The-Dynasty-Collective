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

# #113 / §19.5. This script pulls new code and reinstalls dependencies, then used to launch the
# app with nothing checked in between -- so a pull that broke the engine, or a dependency that
# moved under it, reached the user's live draft board first. The fast tier is ~1.5 seconds and
# loads no data; running it here costs nothing a human would notice and is the difference
# between finding out at startup and finding out mid-draft.
#
# It WARNS rather than blocks, deliberately. This is somebody's own copy of their own app, and
# refusing to start it is a worse failure than starting it with a known problem they were told
# about -- especially mid-draft, which is exactly when they are least able to fix it.
#
# The input-manifest check (§19.4) is deliberately NOT run here. A user's own uploads
# legitimately make their input set differ from the commit's, so it would fire on every launch
# for anyone who actually uses the app -- and a warning that always fires is one nobody reads.
# It belongs where the input set is guaranteed clean: CI, and the suite.
echo "Running the fast test tier (~2s)..."
if ! python -m unittest $(python suite_taxonomy.py --tier fast) > /dev/null 2>&1; then
    echo ""
    echo "  !! The fast test tier FAILED on this version. The app will still start, but"
    echo "  !! something this pull changed is broken. Run this to see what:"
    echo "  !!     python -m unittest \$(python suite_taxonomy.py --tier fast)"
    echo ""
fi

echo "Starting the app..."
streamlit run app.py
