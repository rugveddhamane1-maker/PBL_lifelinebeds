#!/bin/bash
set -e

echo "=========================================================="
echo "   LifeLine - Hospital Bed Availability System"
echo "=========================================================="

# Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest to guarantee zero regressions
echo "Running automated verification suite..."
python3 -m pytest tests/test_api.py -v

echo "Starting server..."
python3 run.py
