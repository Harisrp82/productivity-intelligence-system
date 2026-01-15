"""
Main productivity calculator that combines circadian rhythm and recovery analysis.
Generates hourly productivity scores (0-100) for all 24 hours of the day.
"""

import numpy as np
from datetime import datetime, time
from typing import Dict, List, Tuple
import logging

from .circadian_model import CircadianModel
from .recovery_analyzer import RecoveryAnalyzer

logger = logging.getLogger(__name__)


class ProductivityCalculator:
    """
    Calculates hourly productivity scores based on circadian rhythm and recovery.

    Combines multiple factors:
    - Circadian rhythm (Process C)
    - Sleep pressure/homeostatic drive (Process S)
    - Physiological recovery (HRV, RHR)
    - Sleep quality and duration
    """

    # Weight factors for combining scores
    CIRCADIAN_WEIGHT = 0.50
    RECOVERY_WEIGHT = 0.50

    def __init__(self, typical_wake_time: time = time(7, 0),
                 typical_sleep_time: time = time(23, 0)):
        """
        Initialize productivity calculator.

        Args:
            typical_wake_time: Usual wake time
            typical_sleep_time: Usual bedtime
        """
        self.circadian_model = CircadianModel(typical_wake_time, typical_sleep_time)
        self.recovery_analyzer = RecoveryAnalyzer()

        logger.info("Productivity calculator initialized")

    def calculate_hourly_scores(self, wellness_data: Dict, baseline_data: Dict) -> Dict:
        """
        Calculate productivity scores for all 24 hours of the day.

        Args:
            wellness_data: Today's wellness metrics (sleep, HRV, RHR, etc.)
            baseline_data: 7-day baseline averages

        Returns:
            Dict with hourly scores, peak hours, and metadata
        """
        # Extract sleep timing
        wake_time = self._parse_wake_time(wellness_data)
        sleep_hours = wellness_data.get('sleep_hours', 7.5)

        # Calculate recovery factor (0-1 scale)
        recovery_results = self.recovery_analyzer.calculate_overall_recovery(
            wellness_data, baseline_data
        )
        # Use default of 0.7 if overall_score is None or missing
        recovery_factor = recovery_results.get('overall_score')
        if recovery_factor is None:
            recovery_factor = 0.7
            logger.warning("Using default recovery factor (0.7) due to missing metrics")

        # Calculate circadian alertness profile for 24 hours
        circadian_profile = self.circadian_model.calculate_24hour_profile(
            wake_time, sleep_hours
        )

        # Combine circadian and recovery into productivity scores
        hourly_scores = []

        for hour in range(24):
            circadian_score = circadian_profile[hour]

            # Combine scores with weights
            productivity = (
                self.CIRCADIAN_WEIGHT * circadian_score +
                self.RECOVERY_WEIGHT * recovery_factor
            )

            # Convert to 0-100 scale
            productivity_score = productivity * 100

            hourly_scores.append({
                'hour': hour,
                'score': round(productivity_score, 1),
                'circadian_component': round(circadian_score * 100, 1),
                'recovery_component': round(recovery_factor * 100, 1)
            })

        # Identify peak productivity windows
        peak_hours = self._identify_peak_hours(hourly_scores, top_n=5)
        low_hours = self._identify_low_hours(hourly_scores, bottom_n=3)

        return {
            'hourly_scores': hourly_scores,
            'peak_hours': peak_hours,
            'low_hours': low_hours,
            'recovery_status': recovery_results['status'],
            'recovery_score': round(recovery_factor * 100, 1),
            'average_score': round(np.mean([h['score'] for h in hourly_scores]), 1),
            'wake_time': wake_time.strftime('%H:%M'),
            'sleep_hours': sleep_hours
        }

    def _parse_wake_time(self, wellness_data: Dict) -> time:
        """
        Extract wake time from wellness data.

        Args:
            wellness_data: Wellness metrics with sleep_end timestamp

        Returns:
            Wake time as time object
        """
        sleep_end = wellness_data.get('sleep_end')

        if sleep_end:
            # Parse ISO format timestamp (e.g., "2024-01-15T07:30:00")
            try:
                dt = datetime.fromisoformat(sleep_end.replace('Z', '+00:00'))
                return dt.time()
            except Exception as e:
                logger.warning(f"Could not parse sleep_end timestamp: {e}")

        # Fallback to typical wake time
        return self.circadian_model.typical_wake_time

    def _identify_peak_hours(self, hourly_scores: List[Dict], top_n: int = 5) -> List[Dict]:
        """
        Identify peak productivity hours.

        Args:
            hourly_scores: List of hourly score dicts
            top_n: Number of peak hours to return

        Returns:
            List of peak hour dicts sorted by score (highest first)
        """
        sorted_scores = sorted(hourly_scores, key=lambda x: x['score'], reverse=True)
        peak_hours = sorted_scores[:top_n]

        # Re-sort by hour for chronological display
        peak_hours_chrono = sorted(peak_hours, key=lambda x: x['hour'])

        return peak_hours_chrono

    def _identify_low_hours(self, hourly_scores: List[Dict], bottom_n: int = 3) -> List[Dict]:
        """
        Identify low productivity hours (to avoid).

        Args:
            hourly_scores: List of hourly score dicts
            bottom_n: Number of low hours to return

        Returns:
            List of low hour dicts sorted by score (lowest first)
        """
        sorted_scores = sorted(hourly_scores, key=lambda x: x['score'])
        low_hours = sorted_scores[:bottom_n]

        return low_hours

    def get_time_block_recommendations(self, hourly_scores: List[Dict]) -> List[Dict]:
        """
        Identify continuous high-productivity time blocks.

        Args:
            hourly_scores: List of hourly score dicts

        Returns:
            List of recommended time blocks for focused work
        """
        # Find consecutive hours with score >= 70
        blocks = []
        current_block = None

        for hour_data in hourly_scores:
            hour = hour_data['hour']
            score = hour_data['score']

            if score >= 70:
                if current_block is None:
                    # Start new block
                    current_block = {
                        'start_hour': hour,
                        'end_hour': hour + 1,
                        'avg_score': score,
                        'hours': [hour_data]
                    }
                else:
                    # Extend current block
                    current_block['end_hour'] = hour + 1
                    current_block['hours'].append(hour_data)
            else:
                # End current block if exists
                if current_block and len(current_block['hours']) >= 2:
                    # Calculate average score for block
                    current_block['avg_score'] = round(
                        np.mean([h['score'] for h in current_block['hours']]), 1
                    )
                    blocks.append(current_block)
                current_block = None

        # Add final block if exists
        if current_block and len(current_block['hours']) >= 2:
            current_block['avg_score'] = round(
                np.mean([h['score'] for h in current_block['hours']]), 1
            )
            blocks.append(current_block)

        # Sort by average score
        blocks.sort(key=lambda x: x['avg_score'], reverse=True)

        # Format for output
        formatted_blocks = []
        for block in blocks:
            formatted_blocks.append({
                'time_window': f"{block['start_hour']:02d}:00 - {block['end_hour']:02d}:00",
                'duration_hours': len(block['hours']),
                'avg_score': block['avg_score']
            })

        return formatted_blocks

    def generate_summary_stats(self, productivity_data: Dict) -> Dict:
        """
        Generate summary statistics for the day.

        Args:
            productivity_data: Output from calculate_hourly_scores

        Returns:
            Dict with summary statistics
        """
        hourly_scores = productivity_data['hourly_scores']
        scores = [h['score'] for h in hourly_scores]

        # Count hours by productivity level
        high_productivity = sum(1 for s in scores if s >= 75)
        medium_productivity = sum(1 for s in scores if 60 <= s < 75)
        low_productivity = sum(1 for s in scores if s < 60)

        return {
            'total_high_productivity_hours': high_productivity,
            'total_medium_productivity_hours': medium_productivity,
            'total_low_productivity_hours': low_productivity,
            'best_hour': max(hourly_scores, key=lambda x: x['score']),
            'worst_hour': min(hourly_scores, key=lambda x: x['score']),
            'std_deviation': round(np.std(scores), 1)
        }
