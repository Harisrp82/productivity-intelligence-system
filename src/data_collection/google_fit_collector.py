"""
Google Fit API data collector.
Fetches wellness data including sleep, heart rate, HRV, and steps from Google Fit.

Includes data preprocessing pipeline:
1. Deduplication - Remove duplicate sessions based on session ID
2. Date filtering - Ensure sessions belong to the correct date
3. Validation - Range checks and null handling
4. Outlier detection - Flag unrealistic values
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Data preprocessing pipeline for wellness data.
    Handles deduplication, validation, and outlier detection.
    """

    # Valid ranges for wellness metrics
    VALID_RANGES = {
        'sleep_hours': (0, 24),          # 0-24 hours
        'resting_hr': (30, 120),          # 30-120 bpm
        'hrv_rmssd': (5, 200),            # 5-200 ms
        'steps': (0, 100000),             # 0-100k steps
        'weight': (20, 300),              # 20-300 kg
        'sleep_quality': (1, 5),          # 1-5 rating
    }

    # Reasonable ranges (for outlier flagging, not rejection)
    REASONABLE_RANGES = {
        'sleep_hours': (3, 14),           # 3-14 hours is typical
        'resting_hr': (40, 100),          # 40-100 bpm is typical
        'steps': (100, 50000),            # 100-50k is typical
    }

    def __init__(self):
        """Initialize the preprocessor with a session cache for deduplication."""
        self._processed_session_ids: Set[str] = set()

    def reset_cache(self):
        """Reset the session cache (call when starting a new batch)."""
        self._processed_session_ids.clear()
        logger.debug("Preprocessor cache cleared")

    def is_duplicate_session(self, session_id: str) -> bool:
        """
        Check if a session has already been processed.

        Args:
            session_id: Unique session identifier

        Returns:
            True if duplicate, False otherwise
        """
        if session_id in self._processed_session_ids:
            logger.debug(f"Duplicate session detected: {session_id}")
            return True
        self._processed_session_ids.add(session_id)
        return False

    def validate_value(self, value: Any, metric: str) -> tuple:
        """
        Validate a metric value against valid ranges.

        Args:
            value: The value to validate
            metric: The metric name (e.g., 'sleep_hours')

        Returns:
            Tuple of (is_valid, cleaned_value, warning_message)
        """
        if value is None:
            return True, None, None

        if metric not in self.VALID_RANGES:
            return True, value, None

        min_val, max_val = self.VALID_RANGES[metric]

        # Check if value is within valid range
        if not (min_val <= value <= max_val):
            logger.warning(f"Invalid {metric} value: {value} (valid: {min_val}-{max_val})")
            return False, None, f"Value {value} outside valid range"

        # Check if value is within reasonable range (flag but don't reject)
        warning = None
        if metric in self.REASONABLE_RANGES:
            r_min, r_max = self.REASONABLE_RANGES[metric]
            if not (r_min <= value <= r_max):
                warning = f"Unusual {metric} value: {value}"
                logger.info(warning)

        return True, value, warning

    def filter_sessions_by_date(self, sessions: List[Dict], target_date: datetime) -> List[Dict]:
        """
        Filter sessions to only include those that END on the target date.

        Args:
            sessions: List of session dictionaries
            target_date: The date to filter for

        Returns:
            Filtered list of sessions
        """
        target_date_str = target_date.strftime('%Y-%m-%d')
        filtered = []

        for session in sessions:
            end_ms = int(session.get('endTimeMillis', 0))
            if end_ms:
                end_dt = datetime.fromtimestamp(end_ms / 1000)
                session_date_str = end_dt.strftime('%Y-%m-%d')

                if session_date_str == target_date_str:
                    filtered.append(session)
                else:
                    logger.debug(f"Session filtered out: ends on {session_date_str}, not {target_date_str}")

        return filtered

    def deduplicate_sessions(self, sessions: List[Dict]) -> List[Dict]:
        """
        Remove duplicate sessions based on session ID.

        Args:
            sessions: List of session dictionaries

        Returns:
            Deduplicated list of sessions
        """
        unique_sessions = []
        seen_ids = set()

        for session in sessions:
            session_id = session.get('id') or session.get('name') or str(session.get('startTimeMillis'))

            if session_id not in seen_ids:
                seen_ids.add(session_id)
                unique_sessions.append(session)
            else:
                logger.debug(f"Duplicate session removed: {session_id}")

        if len(sessions) != len(unique_sessions):
            logger.info(f"Deduplication: {len(sessions)} -> {unique_sessions} sessions")

        return unique_sessions

    def preprocess_wellness_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess wellness data with validation and cleaning.

        Args:
            data: Raw wellness data dictionary

        Returns:
            Cleaned and validated wellness data
        """
        cleaned_data = data.copy()
        warnings = []

        # Validate each metric
        for metric in ['sleep_hours', 'resting_hr', 'hrv_rmssd', 'steps', 'weight', 'sleep_quality']:
            if metric in cleaned_data:
                is_valid, cleaned_value, warning = self.validate_value(cleaned_data[metric], metric)
                cleaned_data[metric] = cleaned_value
                if warning:
                    warnings.append(warning)

        # Recalculate sleep_seconds if sleep_hours was modified
        if cleaned_data.get('sleep_hours') is not None:
            cleaned_data['sleep_seconds'] = int(cleaned_data['sleep_hours'] * 3600)

        # Add preprocessing metadata
        cleaned_data['_preprocessing'] = {
            'validated': True,
            'warnings': warnings,
            'processed_at': datetime.utcnow().isoformat()
        }

        return cleaned_data


class GoogleFitCollector:
    """Collects wellness and activity data from Google Fit API."""

    # Scopes required for Google Fit API
    SCOPES = [
        'https://www.googleapis.com/auth/fitness.sleep.read',
        'https://www.googleapis.com/auth/fitness.heart_rate.read',
        'https://www.googleapis.com/auth/fitness.activity.read',
        'https://www.googleapis.com/auth/fitness.body.read',
    ]

    # Data source IDs for different metrics
    DATA_SOURCES = {
        'heart_rate': 'derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm',
        'steps': 'derived:com.google.step_count.delta:com.google.android.gms:estimated_steps',
        'sleep': 'derived:com.google.sleep.segment:com.google.android.gms:merged',
        'weight': 'derived:com.google.weight:com.google.android.gms:merge_weight',
        'hrv': 'derived:com.google.heart_rate.bpm:com.google.android.gms:resting_heart_rate',
    }

    def __init__(self, credentials_path: str = 'credentials.json',
                 token_path: str = 'token_fit.json'):
        """
        Initialize the Google Fit collector.

        Args:
            credentials_path: Path to OAuth credentials JSON
            token_path: Path to store/load access token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None

        # Initialize data preprocessor
        self.preprocessor = DataPreprocessor()

        logger.info("Google Fit collector initialized")

    def authenticate(self) -> bool:
        """
        Authenticate with Google Fit API using OAuth 2.0.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load existing token if available
            if os.path.exists(self.token_path):
                self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                logger.info("Loaded existing Google Fit API credentials")

            # If no valid credentials, initiate OAuth flow
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"Credentials file not found: {self.credentials_path}")
                        return False

                    logger.info("Initiating OAuth flow for Google Fit")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

                # Save credentials for future use
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info("Credentials saved successfully")

            # Build the Fitness API service
            self.service = build('fitness', 'v1', credentials=self.creds)
            logger.info("Google Fit service initialized")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def _get_time_range_millis(self, date: datetime) -> tuple:
        """Get start and end time in milliseconds for a given date."""
        start = datetime(date.year, date.month, date.day, 0, 0, 0)
        end = datetime(date.year, date.month, date.day, 23, 59, 59)

        start_millis = int(start.timestamp() * 1000)
        end_millis = int(end.timestamp() * 1000)

        return start_millis, end_millis

    def _get_time_range_nanos(self, date: datetime) -> tuple:
        """Get start and end time in nanoseconds for a given date."""
        start = datetime(date.year, date.month, date.day, 0, 0, 0)
        end = datetime(date.year, date.month, date.day, 23, 59, 59)

        start_nanos = int(start.timestamp() * 1e9)
        end_nanos = int(end.timestamp() * 1e9)

        return start_nanos, end_nanos

    def get_sleep_data(self, date: datetime) -> Dict[str, Any]:
        """
        Fetch sleep data for a specific date.

        Data Preprocessing Pipeline:
        1. Fetch all sleep sessions in time window
        2. Deduplicate sessions by ID
        3. Filter to only sessions ending on target date
        4. Select primary session (longest duration)
        5. Validate values against valid ranges

        Args:
            date: Date to fetch sleep data for

        Returns:
            Dict with sleep metrics
        """
        try:
            # Sleep sessions are stored for the night ending on this date
            # Query window: previous day 6 PM to target day 6 PM
            start_time = datetime(date.year, date.month, date.day, 0, 0, 0) - timedelta(hours=18)
            end_time = datetime(date.year, date.month, date.day, 18, 0, 0)

            # Step 1: Fetch all sleep sessions in time window
            sessions = self.service.users().sessions().list(
                userId='me',
                startTime=start_time.isoformat() + 'Z',
                endTime=end_time.isoformat() + 'Z',
                activityType=72  # Sleep activity type
            ).execute()

            sleep_sessions = sessions.get('session', [])
            logger.debug(f"Fetched {len(sleep_sessions)} raw sleep sessions for {date.strftime('%Y-%m-%d')}")

            if not sleep_sessions:
                logger.warning(f"No sleep data found for {date.strftime('%Y-%m-%d')}")
                return {
                    'sleep_seconds': None,
                    'sleep_hours': None,
                    'sleep_start': None,
                    'sleep_end': None,
                    'sleep_quality': None
                }

            # Step 2: Deduplicate sessions by ID
            sleep_sessions = self.preprocessor.deduplicate_sessions(sleep_sessions)
            logger.debug(f"After deduplication: {len(sleep_sessions)} sessions")

            # Step 3: Filter to only sessions ending on target date
            sleep_sessions = self.preprocessor.filter_sessions_by_date(sleep_sessions, date)
            logger.debug(f"After date filtering: {len(sleep_sessions)} sessions")

            if not sleep_sessions:
                logger.warning(f"No sleep sessions ending on {date.strftime('%Y-%m-%d')}")
                return {
                    'sleep_seconds': None,
                    'sleep_hours': None,
                    'sleep_start': None,
                    'sleep_end': None,
                    'sleep_quality': None
                }

            # Step 4: Select primary session (prioritize Zepp/Amazfit, then longest duration)
            # Preferred data sources in order of priority
            PREFERRED_SOURCES = [
                'com.huami.watch',      # Zepp/Amazfit
                'com.huami.midong',     # Zepp Life (older Amazfit app)
            ]

            primary_session = None
            max_duration = 0
            preferred_session = None
            preferred_max_duration = 0

            for session in sleep_sessions:
                start_ms = int(session.get('startTimeMillis', 0))
                end_ms = int(session.get('endTimeMillis', 0))
                app_package = session.get('application', {}).get('packageName', '')

                # Calculate duration manually: end time - start time
                duration_ms = end_ms - start_ms

                # Skip sessions with unrealistic durations (> 16 hours)
                if duration_ms > 16 * 60 * 60 * 1000:
                    logger.warning(f"Skipping session with unrealistic duration: {duration_ms / 3600000:.1f}h")
                    continue

                # Check if this is from a preferred source (Zepp/Amazfit)
                if app_package in PREFERRED_SOURCES:
                    if duration_ms > preferred_max_duration:
                        preferred_max_duration = duration_ms
                        preferred_session = session
                        logger.debug(f"Found Zepp session: {duration_ms / 3600000:.1f}h from {app_package}")

                # Also track longest overall as fallback
                if duration_ms > max_duration:
                    max_duration = duration_ms
                    primary_session = session

            # Prefer Zepp session if available, otherwise use longest session
            if preferred_session:
                primary_session = preferred_session
                logger.info(f"Using Zepp/Amazfit sleep data (preferred source)")
            elif primary_session:
                app = primary_session.get('application', {}).get('packageName', 'unknown')
                logger.info(f"No Zepp data found, using fallback source: {app}")

            if not primary_session:
                logger.warning(f"No valid sleep session found for {date.strftime('%Y-%m-%d')}")
                return {
                    'sleep_seconds': None,
                    'sleep_hours': None,
                    'sleep_start': None,
                    'sleep_end': None,
                    'sleep_quality': None
                }

            # Extract start and end times from the primary session
            sleep_start_ms = int(primary_session.get('startTimeMillis', 0))
            sleep_end_ms = int(primary_session.get('endTimeMillis', 0))

            # Calculate duration manually: (end - start)
            total_sleep_ms = sleep_end_ms - sleep_start_ms
            total_sleep_seconds = total_sleep_ms / 1000
            sleep_hours = total_sleep_seconds / 3600

            # Step 5: Validate sleep_hours value
            is_valid, validated_hours, warning = self.preprocessor.validate_value(sleep_hours, 'sleep_hours')
            if not is_valid:
                logger.warning(f"Invalid sleep hours rejected: {sleep_hours}")
                sleep_hours = None
                total_sleep_seconds = None

            # Convert timestamps to ISO format
            sleep_start = datetime.fromtimestamp(sleep_start_ms / 1000).isoformat() if sleep_start_ms else None
            sleep_end = datetime.fromtimestamp(sleep_end_ms / 1000).isoformat() if sleep_end_ms else None

            # Estimate sleep quality based on duration (simple heuristic)
            if sleep_hours >= 7.5:
                sleep_quality = 5
            elif sleep_hours >= 7:
                sleep_quality = 4
            elif sleep_hours >= 6:
                sleep_quality = 3
            elif sleep_hours >= 5:
                sleep_quality = 2
            else:
                sleep_quality = 1

            logger.info(f"Sleep data for {date.strftime('%Y-%m-%d')}: {sleep_hours:.1f} hours")

            return {
                'sleep_seconds': int(total_sleep_seconds),
                'sleep_hours': round(sleep_hours, 2),
                'sleep_start': sleep_start,
                'sleep_end': sleep_end,
                'sleep_quality': sleep_quality
            }

        except HttpError as e:
            logger.error(f"Error fetching sleep data: {e}")
            return {
                'sleep_seconds': None,
                'sleep_hours': None,
                'sleep_start': None,
                'sleep_end': None,
                'sleep_quality': None
            }

    def get_heart_rate_data(self, date: datetime) -> Dict[str, Any]:
        """
        Fetch heart rate data for a specific date.

        Args:
            date: Date to fetch heart rate data for

        Returns:
            Dict with heart rate metrics including resting HR
        """
        try:
            start_nanos, end_nanos = self._get_time_range_nanos(date)

            # Request heart rate data
            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.heart_rate.bpm"
                }],
                "bucketByTime": {"durationMillis": 86400000},  # 24 hours
                "startTimeMillis": int(start_nanos / 1e6),
                "endTimeMillis": int(end_nanos / 1e6)
            }

            response = self.service.users().dataset().aggregate(
                userId='me',
                body=body
            ).execute()

            buckets = response.get('bucket', [])

            all_hr_values = []

            for bucket in buckets:
                for dataset in bucket.get('dataset', []):
                    for point in dataset.get('point', []):
                        for value in point.get('value', []):
                            if 'fpVal' in value:
                                all_hr_values.append(value['fpVal'])

            if not all_hr_values:
                logger.warning(f"No heart rate data found for {date.strftime('%Y-%m-%d')}")
                return {
                    'resting_hr': None,
                    'avg_hr': None,
                    'min_hr': None,
                    'max_hr': None
                }

            # Resting HR is typically the lowest values (bottom 10%)
            sorted_hr = sorted(all_hr_values)
            resting_sample_size = max(1, len(sorted_hr) // 10)
            resting_hr = sum(sorted_hr[:resting_sample_size]) / resting_sample_size

            logger.info(f"Heart rate data for {date.strftime('%Y-%m-%d')}: RHR={resting_hr:.0f}")

            return {
                'resting_hr': round(resting_hr, 1),
                'avg_hr': round(sum(all_hr_values) / len(all_hr_values), 1),
                'min_hr': round(min(all_hr_values), 1),
                'max_hr': round(max(all_hr_values), 1)
            }

        except HttpError as e:
            logger.error(f"Error fetching heart rate data: {e}")
            return {
                'resting_hr': None,
                'avg_hr': None,
                'min_hr': None,
                'max_hr': None
            }

    def get_steps_data(self, date: datetime) -> Optional[int]:
        """
        Fetch step count for a specific date.

        Args:
            date: Date to fetch steps for

        Returns:
            Total steps for the day or None if not available
        """
        try:
            start_nanos, end_nanos = self._get_time_range_nanos(date)

            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.step_count.delta"
                }],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": int(start_nanos / 1e6),
                "endTimeMillis": int(end_nanos / 1e6)
            }

            response = self.service.users().dataset().aggregate(
                userId='me',
                body=body
            ).execute()

            total_steps = 0
            for bucket in response.get('bucket', []):
                for dataset in bucket.get('dataset', []):
                    for point in dataset.get('point', []):
                        for value in point.get('value', []):
                            if 'intVal' in value:
                                total_steps += value['intVal']

            logger.info(f"Steps for {date.strftime('%Y-%m-%d')}: {total_steps}")
            return total_steps if total_steps > 0 else None

        except HttpError as e:
            logger.error(f"Error fetching steps data: {e}")
            return None

    def get_weight_data(self, date: datetime) -> Optional[float]:
        """
        Fetch weight data for a specific date.

        Args:
            date: Date to fetch weight for

        Returns:
            Weight in kg or None if not available
        """
        try:
            start_nanos, end_nanos = self._get_time_range_nanos(date)

            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.weight"
                }],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": int(start_nanos / 1e6),
                "endTimeMillis": int(end_nanos / 1e6)
            }

            response = self.service.users().dataset().aggregate(
                userId='me',
                body=body
            ).execute()

            for bucket in response.get('bucket', []):
                for dataset in bucket.get('dataset', []):
                    for point in dataset.get('point', []):
                        for value in point.get('value', []):
                            if 'fpVal' in value:
                                weight = value['fpVal']
                                logger.info(f"Weight for {date.strftime('%Y-%m-%d')}: {weight:.1f} kg")
                                return round(weight, 1)

            return None

        except HttpError as e:
            logger.error(f"Error fetching weight data: {e}")
            return None

    def get_wellness_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Fetch all wellness data for a specific date.

        Args:
            date: Date to fetch data for

        Returns:
            Dict with all wellness metrics or None if not available
        """
        if not self.service:
            if not self.authenticate():
                logger.error("Failed to authenticate with Google Fit")
                return None

        date_str = date.strftime("%Y-%m-%d")
        logger.info(f"Fetching wellness data from Google Fit for {date_str}")

        # Collect all data
        sleep_data = self.get_sleep_data(date)
        hr_data = self.get_heart_rate_data(date)
        steps = self.get_steps_data(date)
        weight = self.get_weight_data(date)

        wellness = {
            'date': date_str,
            'sleep_seconds': sleep_data.get('sleep_seconds'),
            'sleep_hours': sleep_data.get('sleep_hours'),
            'sleep_quality': sleep_data.get('sleep_quality'),
            'sleep_start': sleep_data.get('sleep_start'),
            'sleep_end': sleep_data.get('sleep_end'),
            'resting_hr': hr_data.get('resting_hr'),
            'hrv_rmssd': None,  # Google Fit doesn't provide HRV directly
            'weight': weight,
            'steps': steps,
            'fatigue': None,
            'mood': None,
            'stress': None,
            'soreness': None,
            'updated': datetime.utcnow().isoformat()
        }

        logger.info(f"Successfully fetched wellness data for {date_str}")
        return wellness

    def get_7day_baseline(self, end_date: datetime) -> Dict[str, float]:
        """
        Calculate 7-day rolling averages for baseline comparison.

        Args:
            end_date: End date for the 7-day window

        Returns:
            Dict with baseline averages for HRV, RHR, sleep
        """
        if not self.service:
            if not self.authenticate():
                return {
                    'avg_hrv': None,
                    'avg_rhr': None,
                    'avg_sleep_hours': None
                }

        start_date = end_date - timedelta(days=6)

        rhr_values = []
        sleep_values = []

        current_date = start_date
        while current_date <= end_date:
            # Get heart rate data
            hr_data = self.get_heart_rate_data(current_date)
            if hr_data.get('resting_hr'):
                rhr_values.append(hr_data['resting_hr'])

            # Get sleep data
            sleep_data = self.get_sleep_data(current_date)
            if sleep_data.get('sleep_hours'):
                sleep_values.append(sleep_data['sleep_hours'])

            current_date += timedelta(days=1)

        return {
            'avg_hrv': None,  # Google Fit doesn't provide HRV
            'avg_rhr': sum(rhr_values) / len(rhr_values) if rhr_values else None,
            'avg_sleep_hours': sum(sleep_values) / len(sleep_values) if sleep_values else None,
            'data_points': max(len(rhr_values), len(sleep_values))
        }

    def collect_daily_data(self, date: datetime) -> Dict[str, Any]:
        """
        Collect all relevant data for a specific date.

        Args:
            date: Date to collect data for

        Returns:
            Complete dataset for the date
        """
        logger.info(f"Collecting daily data from Google Fit for {date.strftime('%Y-%m-%d')}")

        # Authenticate if not already
        if not self.service:
            self.authenticate()

        # Get wellness data for the date
        wellness = self.get_wellness_data(date)

        # Get 7-day baseline for comparison (excluding current day)
        baseline = self.get_7day_baseline(date - timedelta(days=1))

        return {
            'date': date.strftime('%Y-%m-%d'),
            'wellness': wellness,
            'baseline': baseline,
            'recent_activities': [],  # Could be expanded to fetch activities
            'collected_at': datetime.utcnow().isoformat()
        }

    def test_connection(self) -> bool:
        """
        Test the API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.authenticate():
                return False

            # Try to fetch today's data as a test
            today = datetime.now()
            steps = self.get_steps_data(today)

            logger.info(f"Connection successful! Today's steps: {steps or 'No data'}")
            return True

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
