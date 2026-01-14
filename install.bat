@echo off
echo ============================================================
echo Productivity Intelligence System - Installation Script
echo ============================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.11 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

:: Check if .env exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file and add your API keys!
    echo.
    pause
) else (
    echo .env file already exists.
    echo.
)

:: Install dependencies
echo Installing Python dependencies...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Installation complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Edit .env file with your API keys and configuration
echo    - INTERVALS_API_KEY from https://intervals.icu/settings
echo    - ANTHROPIC_API_KEY from https://console.anthropic.com/
echo    - GOOGLE_DOC_ID from your Google Doc URL
echo.
echo 2. Download OAuth credentials:
echo    - Go to https://console.cloud.google.com/
echo    - Enable Google Docs API
echo    - Create OAuth Desktop credentials
echo    - Save as 'credentials.json'
echo.
echo 3. Run setup scripts:
echo    python scripts\setup_database.py
echo    python scripts\setup_google_auth.py
echo.
echo 4. Test your setup:
echo    python scripts\test_data_collection.py
echo    python scripts\test_full_workflow.py
echo.
echo 5. Run your first report:
echo    python daily_workflow.py
echo.
echo See QUICKSTART.md for detailed instructions.
echo.
pause
