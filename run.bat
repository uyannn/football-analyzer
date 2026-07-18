@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Football Analyzer
cd /d "%~dp0"
python -X utf8 -m football_analyzer.main
echo.
pause
