"""
One-time Google OAuth setup for Google Docs API access.

Steps:
1. Download OAuth credentials from Google Cloud Console
2. Save as 'credentials.json' in project root
3. Run this script to authorize and create token
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.delivery import GoogleDocsClient
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Setup Google OAuth authentication."""
    logger.info("Setting up Google Docs API authentication...")

    # Check for credentials file
    credentials_path = 'credentials.json'
    if not os.path.exists(credentials_path):
        logger.error("\n" + "=" * 60)
        logger.error("ERROR: credentials.json not found!")
        logger.error("=" * 60)
        logger.error("\nPlease follow these steps:")
        logger.error("\n1. Go to Google Cloud Console:")
        logger.error("   https://console.cloud.google.com/")
        logger.error("\n2. Create a new project or select existing project")
        logger.error("\n3. Enable Google Docs API:")
        logger.error("   - Go to 'APIs & Services' > 'Library'")
        logger.error("   - Search for 'Google Docs API'")
        logger.error("   - Click 'Enable'")
        logger.error("\n4. Create OAuth credentials:")
        logger.error("   - Go to 'APIs & Services' > 'Credentials'")
        logger.error("   - Click 'Create Credentials' > 'OAuth client ID'")
        logger.error("   - Choose 'Desktop app'")
        logger.error("   - Download the JSON file")
        logger.error("\n5. Rename the downloaded file to 'credentials.json'")
        logger.error("   and place it in the project root directory")
        logger.error("\n6. Run this script again")
        logger.error("\n" + "=" * 60)
        return False

    logger.info("Found credentials.json")

    # Load environment to get doc ID for testing
    load_dotenv()
    doc_id = os.getenv('GOOGLE_DOC_ID')

    # Initialize client
    client = GoogleDocsClient(credentials_path=credentials_path)

    # Run authentication flow
    logger.info("\n" + "=" * 60)
    logger.info("Starting OAuth authentication flow...")
    logger.info("=" * 60)
    logger.info("\nA browser window will open.")
    logger.info("Please:")
    logger.info("  1. Sign in with your Google account")
    logger.info("  2. Grant access to Google Docs")
    logger.info("  3. Return to this terminal")

    if not client.authenticate():
        logger.error("\nAuthentication failed!")
        return False

    logger.info("\n" + "=" * 60)
    logger.info("Authentication successful!")
    logger.info("=" * 60)
    logger.info("\nToken saved to 'token.json'")

    # Test access if doc ID provided
    if doc_id:
        logger.info("\n" + "=" * 60)
        logger.info("Testing access to your Google Doc...")
        logger.info("=" * 60)

        title = client.get_document_title(doc_id)
        if title:
            logger.info(f"\nSuccess! Can access document: '{title}'")
            logger.info("\n" + "=" * 60)
            logger.info("Setup complete!")
            logger.info("=" * 60)
            logger.info("\nYou can now run the full workflow with:")
            logger.info("  python daily_workflow.py")
            return True
        else:
            logger.error("\nCould not access the document.")
            logger.error("Please verify:")
            logger.error("  1. The GOOGLE_DOC_ID in your .env file is correct")
            logger.error("  2. The document exists and is accessible")
            logger.error("  3. You have edit permission for the document")
            return False
    else:
        logger.warning("\nNo GOOGLE_DOC_ID found in .env file")
        logger.info("Authentication is set up, but you need to:")
        logger.info("  1. Create a Google Doc for your reports")
        logger.info("  2. Copy the document ID from the URL")
        logger.info("  3. Add it to your .env file as GOOGLE_DOC_ID")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
