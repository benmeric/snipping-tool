@echo off
title Ekran Alintisi Araci (Google Lens)
cd /d "%~dp0"
echo Ekran Alintisi Araci aciliyor...
python main.py
if errorlevel 1 (
    echo Bir hata olustu.
    pause
)
