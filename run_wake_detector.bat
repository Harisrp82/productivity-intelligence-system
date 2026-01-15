@echo off
REM Wake Detector - Runs automatically via Task Scheduler
REM Checks if you've woken up and generates your daily productivity report

cd /d "D:\Projects\Amazfit Watch Project"

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run wake detector
python wake_detector.py

REM Exit with the same code as Python script
exit /b %ERRORLEVEL%
