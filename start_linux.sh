#!/bin/bash
echo "Starting LiveModules..."

if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Warning: Virtual environment not found, using system Python"
fi

echo "Running start_all.py..."
python start_all.py &

echo "Running live-tts.py..."
python live-tts.py &

echo "All services started!"
wait
