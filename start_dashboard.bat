@echo off
title Productivity Dashboard Server
cd /d "D:\Projects\Amazfit Watch Project"
echo ============================================
echo   Starting Productivity Dashboard Server
echo ============================================
echo.
echo   Dashboard: http://localhost:5000
echo   Press Ctrl+C to stop
echo.
python dashboard_server.py
pause
