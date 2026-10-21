@echo off
title Snipping Tool (Google Lens)
cd /d "%~dp0"
echo Starting Snipping Tool...
python main.py
if errorlevel 1 (
    echo An error occurred.
    pause
)
