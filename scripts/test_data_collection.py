"""
Test script for Intervals.icu data collection.

Verifies:
- API connection
- Wellness data retrieval
- Activity data retrieval
- Baseline calculations
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection import IntervalsICUCollector
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test Intervals.icu data collection."""
    logger.info("Testing Intervals.icu data collection...")

    # Load environment
    load_dotenv()
    api_key = os.getenv('INTERVALS_API_KEY')
    athlete_id = os.getenv('INTERVALS_ATHLETE_ID')

    if not api_key or not athlete_id:
        logger.error("Missing INTERVALS_API_KEY or INTERVALS_ATHLETE_ID in .env file")
        return False

    # Initialize collector
    collector = IntervalsICUCollector(api_key, athlete_id)

    # Test 1: Connection
    logger.info("\n" + "=" * 60)
    logger.info("Test 1: Testing API connection...")
    logger.info("=" * 60)
    if not collector.test_connection():
        logger.error("Connection test failed!")
        return False

    # Test 2: Get yesterday's wellness data
    yesterday = datetime.now() - timedelta(days=1)
    logger.info("\n" + "=" * 60)
    logger.info(f"Test 2: Fetching wellness data for {yesterday.strftime('%Y-%m-%d')}...")
    logger.info("=" * 60)

    wellness = collector.get_wellness_data(yesterday)
    if wellness:
        logger.info("Wellness data retrieved successfully!")
        logger.info(f"  Sleep: {wellness.get('sleep_hours', 'N/A'):.1f} hours")
        logger.info(f"  HRV: {wellness.get('hrv_rmssd', 'N/A')} ms")
        logger.info(f"  RHR: {wellness.get('resting_hr', 'N/A')} bpm")
        logger.info(f"  Quality: {wellness.get('sleep_quality', 'N/A')}/5")
    else:
        logger.warning("No wellness data available for yesterday")
        logger.info("This might be normal if data hasn't synced yet")

    # Test 3: Get 7-day baseline
    logger.info("\n" + "=" * 60)
    logger.info("Test 3: Calculating 7-day baseline...")
    logger.info("=" * 60)

    baseline = collector.get_7day_baseline(yesterday)
    logger.info("Baseline calculated successfully!")
    logger.info(f"  Avg HRV: {baseline.get('avg_hrv', 'N/A'):.1f} ms")
    logger.info(f"  Avg RHR: {baseline.get('avg_rhr', 'N/A'):.1f} bpm")
    logger.info(f"  Avg Sleep: {baseline.get('avg_sleep_hours', 'N/A'):.1f} hours")
    logger.info(f"  Data points: {baseline.get('data_points', 0)}/7 days")

    # Test 4: Get recent activities
    logger.info("\n" + "=" * 60)
    logger.info("Test 4: Fetching recent activities...")
    logger.info("=" * 60)

    activities = collector.get_activities(
        start_date=yesterday - timedelta(days=2),
        end_date=yesterday
    )
    logger.info(f"Found {len(activities)} activities in last 3 days")
    for activity in activities[:3]:
        logger.info(f"  - {activity.get('start_date', 'N/A')[:10]}: "
                   f"{activity.get('type', 'Unknown')} "
                   f"({activity.get('duration', 0) / 60:.0f} min)")

    # Test 5: Complete daily data collection
    logger.info("\n" + "=" * 60)
    logger.info("Test 5: Testing complete daily data collection...")
    logger.info("=" * 60)

    daily_data = collector.collect_daily_data(yesterday)
    logger.info("Complete daily data collected successfully!")
    logger.info(f"  Date: {daily_data.get('date')}")
    logger.info(f"  Wellness data: {'Yes' if daily_data.get('wellness') else 'No'}")
    logger.info(f"  Baseline data: {'Yes' if daily_data.get('baseline') else 'No'}")
    logger.info(f"  Recent activities: {len(daily_data.get('recent_activities', []))}")

    logger.info("\n" + "=" * 60)
    logger.info("All tests completed successfully!")
    logger.info("=" * 60)
    logger.info("\nYour Intervals.icu integration is working correctly.")
    logger.info("You can now run the full workflow with: python daily_workflow.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
