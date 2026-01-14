#!/bin/bash

echo "============================================================"
echo "Productivity Intelligence System - Installation Script"
echo "============================================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

echo "Python found!"
python3 --version
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit .env file and add your API keys!"
    echo ""
    read -p "Press enter to continue..."
else
    echo ".env file already exists."
    echo ""
fi

# Create virtual environment (optional but recommended)
read -p "Create Python virtual environment? (recommended) [Y/n] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        echo "Virtual environment created."
    else
        echo "Virtual environment already exists."
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
echo "Installing Python dependencies..."
echo ""
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install dependencies!"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "============================================================"
echo "Installation complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your API keys and configuration"
echo "   - INTERVALS_API_KEY from https://intervals.icu/settings"
echo "   - ANTHROPIC_API_KEY from https://console.anthropic.com/"
echo "   - GOOGLE_DOC_ID from your Google Doc URL"
echo ""
echo "2. Download OAuth credentials:"
echo "   - Go to https://console.cloud.google.com/"
echo "   - Enable Google Docs API"
echo "   - Create OAuth Desktop credentials"
echo "   - Save as 'credentials.json'"
echo ""
echo "3. Run setup scripts:"
echo "   python scripts/setup_database.py"
echo "   python scripts/setup_google_auth.py"
echo ""
echo "4. Test your setup:"
echo "   python scripts/test_data_collection.py"
echo "   python scripts/test_full_workflow.py"
echo ""
echo "5. Run your first report:"
echo "   python daily_workflow.py"
echo ""
echo "See QUICKSTART.md for detailed instructions."
echo ""

# Make script executable
chmod +x install.sh

echo "If you created a virtual environment, remember to activate it:"
echo "  source venv/bin/activate"
echo ""
