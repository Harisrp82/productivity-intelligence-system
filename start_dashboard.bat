@echo off
title Productivity Dashboard Server
cd /d "D:\Projects\Amazfit Watch Project"
echo ============================================
echo   Productivity Dashboard Server
echo ============================================
echo.
echo   Fetching fresh data from Google Fit...
echo.
python daily_workflow.py
echo.
echo ============================================
echo   Starting Dashboard Server
echo ============================================
echo.
echo   Dashboard: http://localhost:5000
echo   Press Ctrl+C to stop
echo.
python dashboard_server.py
pause
