#!/bin/bash

# Lab 2 Part 2 - System Stop Script

echo "🛑 Deteniendo Lab 2 System..."

# Kill processes by PID if available
if [ -f logs/receiver.pid ]; then
    kill $(cat logs/receiver.pid) 2>/dev/null || true
    rm -f logs/receiver.pid
fi

if [ -f logs/streamlit.pid ]; then
    kill $(cat logs/streamlit.pid) 2>/dev/null || true  
    rm -f logs/streamlit.pid
fi

# Kill by port as backup
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true

echo "✅ Sistema detenido"
