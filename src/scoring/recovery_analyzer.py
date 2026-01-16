"""
Recovery analysis based on HRV, resting heart rate, sleep quality, and sleep debt.
"""

import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RecoveryAnalyzer:
    """
    Analyzes recovery status from physiological metrics.

    Uses HRV (Heart Rate Variability) and RHR (Resting Heart Rate) as primary
    indicators of recovery and autonomic nervous system balance.
    Sleep debt is factored in to account for cumulative sleep deficits.
    """

    # Recovery score weights (adjusted to include sleep debt)
    HRV_WEIGHT = 0.40
    RHR_WEIGHT = 0.30
    SLEEP_QUALITY_WEIGHT = 0.15
    SLEEP_DEBT_WEIGHT = 0.15

    # Standard deviation thresholds for categorization
    HRV_OPTIMAL_THRESHOLD = 0.5  # +0.5 SD above baseline
    HRV_POOR_THRESHOLD = -0.5    # -0.5 SD below baseline
    RHR_OPTIMAL_THRESHOLD = -3.0  # 3 bpm below baseline
    RHR_POOR_THRESHOLD = 3.0      # 3 bpm above baseline

    def __init__(self):
        """Initialize recovery analyzer."""
        logger.info("Recovery analyzer initialized")

    def calculate_hrv_score(self, current_hrv: float, baseline_hrv: float,
                           baseline_std: Optional[float] = None) -> float:
        """
        Calculate recovery score from HRV.

        Higher HRV indicates better recovery and parasympathetic dominance.

        Args:
            current_hrv: Today's HRV RMSSD value (ms)
            baseline_hrv: 7-day average HRV (ms)
            baseline_std: Standard deviation of baseline (optional)

        Returns:
            HRV recovery score (0.0-1.0)
        """
        if baseline_std is None:
            baseline_std = baseline_hrv * 0.15  # Estimate ~15% coefficient of variation

        # Calculate z-score (standard deviations from baseline)
        if baseline_std > 0:
            z_score = (current_hrv - baseline_hrv) / baseline_std
        else:
            z_score = 0.0

        # Map z-score to 0-1 scale
        # +0.5 SD or more = 1.0 (optimal)
        # -0.5 SD or less = 0.0 (poor recovery)
        if z_score >= self.HRV_OPTIMAL_THRESHOLD:
            score = 1.0
        elif z_score <= self.HRV_POOR_THRESHOLD:
            score = 0.0
        else:
            # Linear interpolation between poor and optimal
            score = (z_score - self.HRV_POOR_THRESHOLD) / (
                self.HRV_OPTIMAL_THRESHOLD - self.HRV_POOR_THRESHOLD
            )

        return np.clip(score, 0.0, 1.0)

    def calculate_rhr_score(self, current_rhr: float, baseline_rhr: float) -> float:
        """
        Calculate recovery score from resting heart rate.

        Lower RHR indicates better recovery.

        Args:
            current_rhr: Today's resting heart rate (bpm)
            baseline_rhr: 7-day average RHR (bpm)

        Returns:
            RHR recovery score (0.0-1.0)
        """
        # Calculate deviation from baseline
        deviation = current_rhr - baseline_rhr

        # Map deviation to 0-1 scale
        # -3 bpm or lower = 1.0 (optimal)
        # +3 bpm or higher = 0.0 (poor recovery)
        if deviation <= self.RHR_OPTIMAL_THRESHOLD:
            score = 1.0
        elif deviation >= self.RHR_POOR_THRESHOLD:
            score = 0.0
        else:
            # Linear interpolation
            score = 1.0 - (deviation - self.RHR_OPTIMAL_THRESHOLD) / (
                self.RHR_POOR_THRESHOLD - self.RHR_OPTIMAL_THRESHOLD
            )

        return np.clip(score, 0.0, 1.0)

    def calculate_sleep_score(self, sleep_hours: float, sleep_quality: Optional[int] = None) -> float:
        """
        Calculate sleep recovery score.

        Args:
            sleep_hours: Hours of sleep
            sleep_quality: Subjective quality rating (1-5, optional)

        Returns:
            Sleep recovery score (0.0-1.0)
        """
        # Optimal sleep is 7-9 hours
        if 7.0 <= sleep_hours <= 9.0:
            duration_score = 1.0
        elif sleep_hours < 7.0:
            # Penalty for sleep deprivation (more severe)
            duration_score = max(0.0, sleep_hours / 7.0)
        else:  # sleep_hours > 9.0
            # Slight penalty for oversleeping
            duration_score = max(0.5, 1.0 - (sleep_hours - 9.0) * 0.1)

        # Incorporate sleep quality if available
        if sleep_quality is not None:
            quality_score = (sleep_quality - 1) / 4  # Normalize 1-5 to 0-1
            combined_score = 0.7 * duration_score + 0.3 * quality_score
        else:
            combined_score = duration_score

        return np.clip(combined_score, 0.0, 1.0)

    def calculate_overall_recovery(self, wellness_data: Dict, baseline_data: Dict,
                                    sleep_debt: Optional[float] = None) -> Dict:
        """
        Calculate comprehensive recovery score.

        Args:
            wellness_data: Today's wellness metrics
            baseline_data: 7-day baseline averages
            sleep_debt: Accumulated sleep debt in hours (optional)

        Returns:
            Dict with recovery scores and status
        """
        scores = {}

        # HRV score
        if wellness_data.get('hrv_rmssd') and baseline_data.get('avg_hrv'):
            scores['hrv'] = self.calculate_hrv_score(
                wellness_data['hrv_rmssd'],
                baseline_data['avg_hrv']
            )
        else:
            scores['hrv'] = None
            logger.warning("HRV data not available for recovery calculation")

        # RHR score
        if wellness_data.get('resting_hr') and baseline_data.get('avg_rhr'):
            scores['rhr'] = self.calculate_rhr_score(
                wellness_data['resting_hr'],
                baseline_data['avg_rhr']
            )
        else:
            scores['rhr'] = None
            logger.warning("RHR data not available for recovery calculation")

        # Sleep score
        if wellness_data.get('sleep_hours'):
            scores['sleep'] = self.calculate_sleep_score(
                wellness_data['sleep_hours'],
                wellness_data.get('sleep_quality')
            )
        else:
            scores['sleep'] = None
            logger.warning("Sleep data not available for recovery calculation")

        # Sleep debt score
        if sleep_debt is not None:
            from .sleep_debt_calculator import SleepDebtCalculator
            debt_calculator = SleepDebtCalculator()
            scores['sleep_debt'] = debt_calculator.calculate_debt_impact_factor(sleep_debt)
        else:
            scores['sleep_debt'] = None
            logger.info("Sleep debt not available for recovery calculation")

        # Calculate weighted overall score
        available_scores = [(k, v) for k, v in scores.items() if v is not None]

        if not available_scores:
            logger.error("No recovery metrics available")
            return {
                'overall_score': None,
                'hrv_score': None,
                'rhr_score': None,
                'sleep_score': None,
                'sleep_debt_score': None,
                'sleep_debt': sleep_debt,
                'status': 'unknown',
                'available_metrics': 0
            }

        # Recalculate weights based on available metrics
        weights = {
            'hrv': self.HRV_WEIGHT,
            'rhr': self.RHR_WEIGHT,
            'sleep': self.SLEEP_QUALITY_WEIGHT,
            'sleep_debt': self.SLEEP_DEBT_WEIGHT
        }

        total_weight = sum(weights[k] for k, _ in available_scores)
        normalized_weights = {k: weights[k] / total_weight for k, _ in available_scores}

        overall_score = sum(v * normalized_weights[k] for k, v in available_scores)

        # Determine recovery status
        if overall_score >= 0.75:
            status = 'excellent'
        elif overall_score >= 0.60:
            status = 'good'
        elif overall_score >= 0.45:
            status = 'moderate'
        elif overall_score >= 0.30:
            status = 'poor'
        else:
            status = 'very_poor'

        return {
            'overall_score': overall_score,
            'hrv_score': scores['hrv'],
            'rhr_score': scores['rhr'],
            'sleep_score': scores['sleep'],
            'sleep_debt_score': scores.get('sleep_debt'),
            'sleep_debt': sleep_debt,
            'status': status,
            'available_metrics': len(available_scores)
        }

    def get_recovery_insights(self, recovery_data: Dict, wellness_data: Dict,
                             baseline_data: Dict) -> list:
        """
        Generate human-readable insights from recovery analysis.

        Args:
            recovery_data: Output from calculate_overall_recovery
            wellness_data: Today's wellness metrics
            baseline_data: Baseline metrics

        Returns:
            List of insight strings
        """
        insights = []

        # Overall status insight
        status = recovery_data['status']
        status_messages = {
            'excellent': 'Your recovery is excellent. Your body is well-rested and ready for high performance.',
            'good': 'Your recovery is good. You should have solid energy levels today.',
            'moderate': 'Your recovery is moderate. Consider managing intensity today.',
            'poor': 'Your recovery is below average. Prioritize rest and light activity.',
            'very_poor': 'Your recovery is poor. Focus on rest and recovery activities today.'
        }
        insights.append(status_messages.get(status, 'Recovery status unknown.'))

        # HRV insight
        if recovery_data['hrv_score'] is not None:
            hrv_current = wellness_data.get('hrv_rmssd')
            hrv_baseline = baseline_data.get('avg_hrv')
            hrv_diff = hrv_current - hrv_baseline

            if recovery_data['hrv_score'] >= 0.75:
                insights.append(f'HRV is elevated (+{hrv_diff:.1f}ms), indicating strong parasympathetic activity.')
            elif recovery_data['hrv_score'] <= 0.25:
                insights.append(f'HRV is suppressed ({hrv_diff:+.1f}ms), suggesting incomplete recovery or stress.')

        # RHR insight
        if recovery_data['rhr_score'] is not None:
            rhr_current = wellness_data.get('resting_hr')
            rhr_baseline = baseline_data.get('avg_rhr')
            rhr_diff = rhr_current - rhr_baseline

            if recovery_data['rhr_score'] >= 0.75:
                insights.append(f'Resting heart rate is low ({rhr_diff:+.1f} bpm), showing good recovery.')
            elif recovery_data['rhr_score'] <= 0.25:
                insights.append(f'Resting heart rate is elevated (+{abs(rhr_diff):.1f} bpm), indicating fatigue or stress.')

        # Sleep insight
        if recovery_data['sleep_score'] is not None:
            sleep_hours = wellness_data.get('sleep_hours')

            if sleep_hours < 7:
                deficit = 7.5 - sleep_hours
                insights.append(f'Sleep was {deficit:.1f}h below optimal. This may impact cognitive performance.')
            elif sleep_hours > 9.5:
                insights.append('Sleep duration was longer than typical. May indicate recovery debt or oversleeping.')

        return insights
