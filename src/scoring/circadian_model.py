"""
Circadian rhythm modeling for productivity prediction.
Based on two-process model of sleep regulation (Borbély, 1982).

Enhanced with adaptive wake-time based energy prediction.
"""

import numpy as np
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class CircadianModel:
    """
    Models circadian rhythm using homeostatic sleep drive and circadian process.

    The two-process model:
    - Process S (Sleep Pressure): Builds up during wake, dissipates during sleep
    - Process C (Circadian): 24-hour rhythm with peaks and troughs

    ADAPTIVE MODEL: Energy peaks and troughs are calculated relative to actual
    wake time, not fixed clock times. This accounts for variable sleep schedules.

    Typical energy pattern after waking:
    - First Peak: 2-4 hours after waking (morning alertness)
    - Dip: 6-8 hours after waking (post-lunch slump)
    - Second Peak: 9-11 hours after waking (afternoon surge)
    - Decline: 12+ hours after waking (evening fatigue)
    """

    # Adaptive circadian parameters (hours AFTER waking)
    FIRST_PEAK_HOURS_AFTER_WAKE = 3.0    # Peak alertness ~3 hours after waking
    DIP_HOURS_AFTER_WAKE = 7.0           # Energy dip ~7 hours after waking
    SECOND_PEAK_HOURS_AFTER_WAKE = 10.0  # Second peak ~10 hours after waking
    DECLINE_START_HOURS = 14.0           # Decline starts ~14 hours after waking

    # Energy level parameters
    FIRST_PEAK_INTENSITY = 0.95    # First peak is strongest
    SECOND_PEAK_INTENSITY = 0.85  # Second peak slightly lower
    DIP_INTENSITY = 0.55          # Energy dip level
    BASELINE_ENERGY = 0.70        # Baseline between peaks

    # Sleep pressure parameters
    SLEEP_PRESSURE_BUILDUP_RATE = 1.0 / 16  # Full buildup over 16 hours awake
    SLEEP_PRESSURE_DECAY_RATE = 1.0 / 8     # Full recovery over 8 hours sleep

    def __init__(self, typical_wake_time: time = time(7, 0),
                 typical_sleep_time: time = time(23, 0)):
        """
        Initialize circadian model with typical sleep schedule.

        Args:
            typical_wake_time: Usual wake time
            typical_sleep_time: Usual bedtime
        """
        self.typical_wake_time = typical_wake_time
        self.typical_sleep_time = typical_sleep_time

        logger.info(f"Circadian model initialized: Wake {typical_wake_time}, Sleep {typical_sleep_time}")

    def calculate_circadian_phase(self, hour: float, wake_time: Optional[time] = None) -> float:
        """
        Calculate circadian alertness factor for a given hour (0-24).

        ADAPTIVE: If wake_time is provided, calculates energy based on
        hours since waking rather than fixed clock times.

        Args:
            hour: Hour of day (0-23.99)
            wake_time: Actual wake time (if provided, uses adaptive model)

        Returns:
            Circadian factor (0.0-1.0), where 1.0 is peak alertness
        """
        if wake_time is not None:
            # Use adaptive model based on hours since waking
            return self._calculate_adaptive_energy(hour, wake_time)

        # Fallback to fixed model (legacy behavior)
        return self._calculate_fixed_circadian(hour)

    def _calculate_fixed_circadian(self, hour: float) -> float:
        """Legacy fixed circadian calculation (assumes 7 AM wake time)."""
        CIRCADIAN_PEAK_HOUR = 10.0
        CIRCADIAN_AMPLITUDE = 0.30
        POST_LUNCH_DIP_HOUR = 14.5
        POST_LUNCH_DIP_MAGNITUDE = 0.15

        phase_shift = (CIRCADIAN_PEAK_HOUR - 6) / 24 * 2 * np.pi
        base_rhythm = np.sin(2 * np.pi * hour / 24 - phase_shift)
        circadian_factor = (base_rhythm + 1) / 2

        # Afternoon dip
        dip = POST_LUNCH_DIP_MAGNITUDE * np.exp(
            -((hour - POST_LUNCH_DIP_HOUR) ** 2) / (2 * 2.0 ** 2)
        )
        circadian_factor = max(0.0, circadian_factor - dip)
        circadian_factor = 0.5 + (circadian_factor - 0.5) * (1 + CIRCADIAN_AMPLITUDE)

        return np.clip(circadian_factor, 0.0, 1.0)

    def _calculate_adaptive_energy(self, hour: float, wake_time: time) -> float:
        """
        Calculate energy level based on hours since waking (ADAPTIVE MODEL).

        This shifts the entire energy curve based on actual wake time.

        Args:
            hour: Current hour of day (0-23.99)
            wake_time: Actual wake time

        Returns:
            Energy factor (0.0-1.0)
        """
        wake_hour = wake_time.hour + wake_time.minute / 60
        hours_awake = hour - wake_hour

        # Handle day wrap-around
        if hours_awake < 0:
            hours_awake += 24

        # Before waking or asleep - minimal energy
        if hours_awake > 18 or hours_awake < 0:
            return 0.2

        # Energy curve based on hours since waking
        # Using a combination of Gaussian peaks and decay

        # First peak: ~3 hours after waking
        first_peak = self.FIRST_PEAK_INTENSITY * np.exp(
            -((hours_awake - self.FIRST_PEAK_HOURS_AFTER_WAKE) ** 2) / (2 * 1.5 ** 2)
        )

        # Energy dip: ~7 hours after waking
        dip_effect = (self.BASELINE_ENERGY - self.DIP_INTENSITY) * np.exp(
            -((hours_awake - self.DIP_HOURS_AFTER_WAKE) ** 2) / (2 * 1.5 ** 2)
        )

        # Second peak: ~10 hours after waking
        second_peak = self.SECOND_PEAK_INTENSITY * np.exp(
            -((hours_awake - self.SECOND_PEAK_HOURS_AFTER_WAKE) ** 2) / (2 * 1.5 ** 2)
        )

        # Gradual decline after 14+ hours
        if hours_awake > self.DECLINE_START_HOURS:
            decline_factor = 1.0 - (hours_awake - self.DECLINE_START_HOURS) * 0.1
            decline_factor = max(0.3, decline_factor)
        else:
            decline_factor = 1.0

        # Combine components
        energy = self.BASELINE_ENERGY + first_peak + second_peak - dip_effect
        energy = energy * decline_factor

        # Wake-up ramp (first 30 mins have lower energy)
        if hours_awake < 0.5:
            energy = energy * (0.5 + hours_awake)

        return np.clip(energy, 0.1, 1.0)

    def get_energy_flow_prediction(self, wake_time: time, sleep_hours: float) -> Dict:
        """
        Generate complete energy flow prediction for the day based on wake time.

        Args:
            wake_time: Actual wake time
            sleep_hours: Hours of sleep obtained

        Returns:
            Dict with energy windows, peaks, dips, and recommendations
        """
        wake_hour = wake_time.hour + wake_time.minute / 60

        # Calculate key time points based on wake time
        first_peak_time = (wake_hour + self.FIRST_PEAK_HOURS_AFTER_WAKE) % 24
        dip_time = (wake_hour + self.DIP_HOURS_AFTER_WAKE) % 24
        second_peak_time = (wake_hour + self.SECOND_PEAK_HOURS_AFTER_WAKE) % 24
        decline_time = (wake_hour + self.DECLINE_START_HOURS) % 24

        # Adjust energy levels based on sleep quality
        sleep_factor = min(1.0, sleep_hours / 7.5)  # 7.5 hours = optimal

        # Define high energy windows (for deep work)
        high_energy_windows = [
            {
                'name': 'Morning Peak',
                'start': self._format_hour(wake_hour + 1.5),
                'end': self._format_hour(wake_hour + 4.5),
                'hours_after_wake': '1.5 - 4.5 hours',
                'energy_level': round(self.FIRST_PEAK_INTENSITY * sleep_factor * 100),
                'best_for': 'Deep focused work, complex problem solving'
            },
            {
                'name': 'Afternoon Peak',
                'start': self._format_hour(wake_hour + 8.5),
                'end': self._format_hour(wake_hour + 11.5),
                'hours_after_wake': '8.5 - 11.5 hours',
                'energy_level': round(self.SECOND_PEAK_INTENSITY * sleep_factor * 100),
                'best_for': 'Creative work, collaboration, second deep work session'
            }
        ]

        # Define low energy windows (avoid deep work)
        low_energy_windows = [
            {
                'name': 'Post-Lunch Dip',
                'start': self._format_hour(wake_hour + 6),
                'end': self._format_hour(wake_hour + 8),
                'hours_after_wake': '6 - 8 hours',
                'energy_level': round(self.DIP_INTENSITY * sleep_factor * 100),
                'best_for': 'Light tasks, emails, breaks, naps'
            },
            {
                'name': 'Evening Decline',
                'start': self._format_hour(wake_hour + 14),
                'end': self._format_hour(wake_hour + 16),
                'hours_after_wake': '14+ hours',
                'energy_level': round(0.45 * sleep_factor * 100),
                'best_for': 'Wind down, planning for tomorrow, light reading'
            }
        ]

        return {
            'wake_time': wake_time.strftime('%H:%M'),
            'sleep_hours': sleep_hours,
            'sleep_quality_factor': round(sleep_factor, 2),
            'high_energy_windows': high_energy_windows,
            'low_energy_windows': low_energy_windows,
            'peak_times': {
                'first_peak': self._format_hour(first_peak_time),
                'second_peak': self._format_hour(second_peak_time),
                'energy_dip': self._format_hour(dip_time),
                'decline_starts': self._format_hour(decline_time)
            },
            'summary': f"Based on waking at {wake_time.strftime('%H:%M')}, your peak energy windows are around {self._format_hour(first_peak_time)} and {self._format_hour(second_peak_time)}. Avoid demanding tasks around {self._format_hour(dip_time)}."
        }

    def _format_hour(self, hour: float) -> str:
        """Format hour as HH:MM string."""
        hour = hour % 24
        hours = int(hour)
        minutes = int((hour - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def _calculate_afternoon_dip(self, hour: float) -> float:
        """Calculate the afternoon dip in alertness (legacy method)."""
        POST_LUNCH_DIP_HOUR = 14.5
        POST_LUNCH_DIP_MAGNITUDE = 0.15
        dip_width = 2.0

        dip = POST_LUNCH_DIP_MAGNITUDE * np.exp(
            -((hour - POST_LUNCH_DIP_HOUR) ** 2) / (2 * dip_width ** 2)
        )

        return dip

    def calculate_sleep_pressure(self, hour: float, wake_time: Optional[time] = None,
                                 sleep_hours: Optional[float] = None) -> float:
        """
        Calculate homeostatic sleep pressure (Process S).

        Args:
            hour: Current hour of day (0-23.99)
            wake_time: Actual wake time (uses typical if not provided)
            sleep_hours: Hours of sleep obtained (uses 8 if not provided)

        Returns:
            Sleep pressure (0.0-1.0), where 0.0 is fully rested, 1.0 is maximum fatigue
        """
        if wake_time is None:
            wake_time = self.typical_wake_time

        if sleep_hours is None:
            sleep_hours = 8.0

        # Calculate hours since wake
        wake_hour = wake_time.hour + wake_time.minute / 60
        hours_awake = hour - wake_hour

        # Handle day wrap-around
        if hours_awake < 0:
            hours_awake += 24

        # Sleep pressure builds up linearly with time awake
        base_pressure = hours_awake * self.SLEEP_PRESSURE_BUILDUP_RATE

        # Adjust for sleep quality/quantity
        # Less than 7 hours increases baseline pressure
        sleep_deficit_factor = max(0, (7.5 - sleep_hours) / 7.5) * 0.3
        pressure = base_pressure + sleep_deficit_factor

        return np.clip(pressure, 0.0, 1.0)

    def calculate_hourly_alertness(self, hour: float, wake_time: time,
                                  sleep_hours: float) -> float:
        """
        Calculate overall alertness score for a specific hour.

        Uses ADAPTIVE circadian rhythm based on actual wake time,
        combined with sleep pressure.

        Args:
            hour: Hour of day (0-23.99)
            wake_time: Actual wake time
            sleep_hours: Hours of sleep obtained

        Returns:
            Alertness score (0.0-1.0)
        """
        # Use adaptive circadian calculation based on wake time
        circadian = self.calculate_circadian_phase(hour, wake_time)
        pressure = self.calculate_sleep_pressure(hour, wake_time, sleep_hours)

        # Alertness is circadian boost minus sleep pressure
        alertness = circadian * (1.0 - pressure * 0.5)

        # Adjust for sleep quality
        sleep_factor = min(1.0, sleep_hours / 7.5)
        alertness = alertness * (0.7 + 0.3 * sleep_factor)

        return np.clip(alertness, 0.0, 1.0)

    def calculate_24hour_profile(self, wake_time: time, sleep_hours: float) -> np.ndarray:
        """
        Generate 24-hour alertness profile.

        Args:
            wake_time: Actual wake time
            sleep_hours: Hours of sleep obtained

        Returns:
            Array of 24 alertness scores (one per hour)
        """
        profile = np.zeros(24)

        for hour in range(24):
            profile[hour] = self.calculate_hourly_alertness(hour, wake_time, sleep_hours)

        return profile

    def get_optimal_hours(self, wake_time: time, sleep_hours: float, top_n: int = 5) -> list:
        """
        Identify optimal productivity hours for the day.

        Args:
            wake_time: Actual wake time
            sleep_hours: Hours of sleep obtained
            top_n: Number of best hours to return

        Returns:
            List of tuples (hour, alertness_score)
        """
        profile = self.calculate_24hour_profile(wake_time, sleep_hours)

        # Get top N hours with highest alertness
        top_indices = np.argsort(profile)[-top_n:][::-1]
        optimal_hours = [(hour, profile[hour]) for hour in top_indices]

        return optimal_hours
