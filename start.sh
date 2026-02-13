#!/bin/bash

# Start the Scheduler in background
echo "Starting News Scheduler..."
python -u src/scheduler_runner.py &

# Start the Streamlit Dashboard in foreground
echo "Starting Streamlit Dashboard..."
streamlit run src/dashboard.py --server.port=8501 --server.address=0.0.0.0
