"""
Initialize the SQLite database with all required tables.

Run this once before using the system.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseConnection
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize database."""
    logger.info("Setting up productivity intelligence database...")

    # Load environment
    load_dotenv()
    database_url = os.getenv('DATABASE_URL', 'sqlite:///productivity.db')

    logger.info(f"Database URL: {database_url}")

    # Initialize connection
    db = DatabaseConnection(database_url)

    # Test connection
    if not db.test_connection():
        logger.error("Database connection test failed!")
        return False

    # Create tables
    logger.info("Creating database tables...")
    db.create_tables()

    logger.info("Database setup complete!")
    logger.info("Tables created:")
    logger.info("  - wellness_records: Stores daily wellness metrics")
    logger.info("  - productivity_scores: Stores hourly productivity scores")
    logger.info("  - daily_reports: Stores generated AI reports")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
