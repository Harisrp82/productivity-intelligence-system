"""
Intervals.icu API data collector.
Fetches wellness data including sleep, HRV, RHR from Intervals.icu API.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class IntervalsICUCollector:
    """Collects wellness and activity data from Intervals.icu API."""

    BASE_URL = "https://intervals.icu/api/v1"

    def __init__(self, api_key: str, athlete_id: str):
        """
        Initialize the Intervals.icu collector.

        Args:
            api_key: Intervals.icu API key
            athlete_id: Athlete ID (e.g., 'i123456')
        """
        self.api_key = api_key
        self.athlete_id = athlete_id
        self.session = requests.Session()
        self.session.auth = ("API_KEY", api_key)

    def get_wellness_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Fetch wellness data for a specific date.

        Args:
            date: Date to fetch data for

        Returns:
            Dict with wellness metrics or None if not available
        """
        date_str = date.strftime("%Y-%m-%d")
        url = f"{self.BASE_URL}/athlete/{self.athlete_id}/wellness/{date_str}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            logger.info(f"Successfully fetched wellness data for {date_str}")
            return self._parse_wellness_data(data)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No wellness data found for {date_str}")
                return None
            logger.error(f"HTTP error fetching wellness data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching wellness data for {date_str}: {e}")
            raise

    def _parse_wellness_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Parse raw API response into standardized wellness data."""
        return {
            'date': raw_data.get('id'),
            'sleep_seconds': raw_data.get('sleepSecs'),
            'sleep_hours': raw_data.get('sleepSecs', 0) / 3600 if raw_data.get('sleepSecs') else None,
            'sleep_quality': raw_data.get('sleepQuality'),
            'resting_hr': raw_data.get('restingHR'),
            'hrv_rmssd': raw_data.get('hrvRMSSD'),
            'weight': raw_data.get('weight'),
            'fatigue': raw_data.get('fatigue'),
            'mood': raw_data.get('mood'),
            'stress': raw_data.get('stress'),
            'soreness': raw_data.get('soreness'),
            'sleep_start': raw_data.get('sleepStart'),
            'sleep_end': raw_data.get('sleepEnd'),
            'updated': raw_data.get('updated')
        }

    def get_activities(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch activities within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of activity dictionaries
        """
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        url = f"{self.BASE_URL}/athlete/{self.athlete_id}/activities"

        try:
            response = self.session.get(url, params={
                'oldest': start_str,
                'newest': end_str
            })
            response.raise_for_status()
            activities = response.json()

            logger.info(f"Fetched {len(activities)} activities from {start_str} to {end_str}")
            return [self._parse_activity(a) for a in activities]

        except Exception as e:
            logger.error(f"Error fetching activities: {e}")
            raise

    def _parse_activity(self, raw_data: Dict) -> Dict[str, Any]:
        """Parse raw activity data into standardized format."""
        return {
            'id': raw_data.get('id'),
            'start_date': raw_data.get('start_date_local'),
            'type': raw_data.get('type'),
            'name': raw_data.get('name'),
            'duration': raw_data.get('moving_time'),
            'distance': raw_data.get('distance'),
            'training_load': raw_data.get('icu_training_load'),
            'intensity': raw_data.get('icu_intensity'),
            'avg_hr': raw_data.get('average_heartrate')
        }

    def get_7day_baseline(self, end_date: datetime) -> Dict[str, float]:
        """
        Calculate 7-day rolling averages for baseline comparison.

        Args:
            end_date: End date for the 7-day window

        Returns:
            Dict with baseline averages for HRV, RHR, sleep
        """
        start_date = end_date - timedelta(days=6)

        wellness_data = []
        current_date = start_date

        while current_date <= end_date:
            data = self.get_wellness_data(current_date)
            if data:
                wellness_data.append(data)
            current_date += timedelta(days=1)

        if not wellness_data:
            logger.warning("No wellness data available for baseline calculation")
            return {
                'avg_hrv': None,
                'avg_rhr': None,
                'avg_sleep_hours': None
            }

        # Calculate averages
        hrv_values = [d['hrv_rmssd'] for d in wellness_data if d.get('hrv_rmssd')]
        rhr_values = [d['resting_hr'] for d in wellness_data if d.get('resting_hr')]
        sleep_values = [d['sleep_hours'] for d in wellness_data if d.get('sleep_hours')]

        return {
            'avg_hrv': sum(hrv_values) / len(hrv_values) if hrv_values else None,
            'avg_rhr': sum(rhr_values) / len(rhr_values) if rhr_values else None,
            'avg_sleep_hours': sum(sleep_values) / len(sleep_values) if sleep_values else None,
            'data_points': len(wellness_data)
        }

    def collect_daily_data(self, date: datetime) -> Dict[str, Any]:
        """
        Collect all relevant data for a specific date.

        This is the main method that combines wellness data, baseline metrics,
        and recent activities into a comprehensive dataset.

        Args:
            date: Date to collect data for

        Returns:
            Complete dataset for the date
        """
        logger.info(f"Collecting daily data for {date.strftime('%Y-%m-%d')}")

        # Get wellness data for the date
        wellness = self.get_wellness_data(date)

        # Get 7-day baseline for comparison (excluding current day)
        # Use the day before 'date' as the end of the baseline window
        baseline = self.get_7day_baseline(date - timedelta(days=1))

        # Get recent activities (last 3 days for context)
        activities = self.get_activities(
            start_date=date - timedelta(days=2),
            end_date=date
        )

        return {
            'date': date.strftime('%Y-%m-%d'),
            'wellness': wellness,
            'baseline': baseline,
            'recent_activities': activities,
            'collected_at': datetime.utcnow().isoformat()
        }

    def test_connection(self) -> bool:
        """
        Test the API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/athlete/{self.athlete_id}"
            response = self.session.get(url)
            response.raise_for_status()

            athlete_data = response.json()
            logger.info(f"Connection successful! Athlete: {athlete_data.get('name', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
