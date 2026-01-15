"""
Wake Detection Service for Productivity Intelligence System.

This script runs periodically (via Task Scheduler) and:
1. Checks if today's report has already been generated
2. Detects when you wake up by checking Google Fit sleep data
3. Waits for data to sync, then runs the full workflow
4. Sends your personalized report to Google Docs

Designed for variable wake times (e.g., 8 AM - 2 PM).
"""

import os
import sys
import json
import logging
import time as time_module
from datetime import datetime, timedelta, time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv

# Configure logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'wake_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('wake_detector')

# State file to track daily status
STATE_FILE = Path(__file__).parent / '.wake_detector_state.json'

# Configuration
SYNC_WAIT_MINUTES = 30  # Wait time after wake detection for data to sync
MIN_SLEEP_HOURS = 3.0   # Minimum sleep duration to consider valid


class WakeDetector:
    """Detects wake time and triggers the daily workflow."""

    def __init__(self):
        """Initialize wake detector."""
        load_dotenv()
        self.state = self._load_state()
        self.collector = None

    def _load_state(self) -> dict:
        """Load state from file."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        return {}

    def _save_state(self):
        """Save state to file."""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def _get_today_key(self) -> str:
        """Get today's date as state key."""
        return datetime.now().strftime('%Y-%m-%d')

    def is_already_processed_today(self) -> bool:
        """Check if today's workflow has already run."""
        today_key = self._get_today_key()
        return self.state.get(today_key, {}).get('processed', False)

    def mark_processed_today(self, wake_time: str):
        """Mark today as processed."""
        today_key = self._get_today_key()
        self.state[today_key] = {
            'processed': True,
            'wake_time': wake_time,
            'processed_at': datetime.now().isoformat()
        }
        self._save_state()

        # Clean up old entries (keep last 7 days)
        cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        self.state = {k: v for k, v in self.state.items() if k >= cutoff}
        self._save_state()

    def initialize_collector(self) -> bool:
        """Initialize Google Fit collector."""
        try:
            from data_collection import GoogleFitCollector
            self.collector = GoogleFitCollector()
            return self.collector.authenticate()
        except Exception as e:
            logger.error(f"Failed to initialize collector: {e}")
            return False

    def detect_wake(self) -> tuple:
        """
        Detect if user has woken up today.

        Returns:
            Tuple of (wake_detected: bool, wake_time: datetime or None, sleep_hours: float or None)
        """
        if not self.collector:
            if not self.initialize_collector():
                return False, None, None

        try:
            today = datetime.now()
            sleep_data = self.collector.get_sleep_data(today)

            # Check if we have valid sleep data
            if not sleep_data.get('sleep_end'):
                logger.info("No sleep end time found - user may still be asleep")
                return False, None, None

            sleep_hours = sleep_data.get('sleep_hours', 0)
            if sleep_hours < MIN_SLEEP_HOURS:
                logger.info(f"Sleep duration ({sleep_hours}h) below minimum ({MIN_SLEEP_HOURS}h) - may be a nap")
                return False, None, None

            # Parse wake time
            sleep_end_str = sleep_data['sleep_end']
            wake_time = datetime.fromisoformat(sleep_end_str.replace('Z', '+00:00'))

            # Check if wake time is today
            if wake_time.date() != today.date():
                logger.info(f"Wake time ({wake_time.date()}) is not today")
                return False, None, None

            # Check if wake time is recent (within last 6 hours)
            hours_since_wake = (datetime.now() - wake_time.replace(tzinfo=None)).total_seconds() / 3600
            if hours_since_wake > 6:
                logger.info(f"Wake time was {hours_since_wake:.1f} hours ago - may be old data")
                # Still return true but log warning

            logger.info(f"Wake detected! Time: {wake_time.strftime('%H:%M')}, Sleep: {sleep_hours:.1f}h")
            return True, wake_time, sleep_hours

        except Exception as e:
            logger.error(f"Error detecting wake: {e}")
            return False, None, None

    def run_workflow(self):
        """Run the full daily workflow."""
        logger.info("Starting daily workflow...")

        try:
            from daily_workflow import DailyWorkflow

            workflow = DailyWorkflow()
            success = workflow.run(datetime.now())

            if success:
                logger.info("Daily workflow completed successfully!")
            else:
                logger.error("Daily workflow failed!")

            return success

        except Exception as e:
            logger.error(f"Error running workflow: {e}")
            return False

    def run(self):
        """
        Main entry point for wake detection.

        Returns:
            0 if successful or already processed
            1 if wake not detected yet
            2 if error occurred
        """
        logger.info("=" * 60)
        logger.info("Wake Detector - Checking for wake...")
        logger.info("=" * 60)

        # Check if already processed today
        if self.is_already_processed_today():
            today_state = self.state.get(self._get_today_key(), {})
            logger.info(f"Already processed today at {today_state.get('processed_at', 'unknown')}")
            logger.info(f"Wake time was: {today_state.get('wake_time', 'unknown')}")
            return 0

        # Detect wake
        wake_detected, wake_time, sleep_hours = self.detect_wake()

        if not wake_detected:
            logger.info("Wake not detected yet. Will check again later.")
            return 1

        # Wake detected! Wait for data to sync
        logger.info(f"Wake detected at {wake_time.strftime('%H:%M')}!")
        logger.info(f"Sleep duration: {sleep_hours:.1f} hours")
        logger.info(f"Waiting {SYNC_WAIT_MINUTES} minutes for data to sync...")

        # Calculate time since wake
        time_since_wake = (datetime.now() - wake_time.replace(tzinfo=None)).total_seconds() / 60

        if time_since_wake < SYNC_WAIT_MINUTES:
            wait_time = SYNC_WAIT_MINUTES - time_since_wake
            logger.info(f"Waiting {wait_time:.0f} more minutes for data sync...")
            time_module.sleep(wait_time * 60)
        else:
            logger.info(f"Already {time_since_wake:.0f} minutes since wake - proceeding immediately")

        # Run the workflow
        logger.info("Running daily workflow...")
        success = self.run_workflow()

        if success:
            # Mark as processed
            self.mark_processed_today(wake_time.strftime('%H:%M'))
            logger.info("=" * 60)
            logger.info("SUCCESS! Daily report generated and sent to Google Docs")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("Workflow failed - will retry on next run")
            return 2


def main():
    """Main entry point."""
    detector = WakeDetector()
    exit_code = detector.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
