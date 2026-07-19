@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
title Football Analyzer
cd /d "%~dp0"
python -X utf8 -u -m football_analyzer.main
echo.
pause
