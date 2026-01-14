"""
Circadian rhythm modeling for productivity prediction.
Based on two-process model of sleep regulation (Borbély, 1982).
"""

import numpy as np
from datetime import datetime, time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CircadianModel:
    """
    Models circadian rhythm using homeostatic sleep drive and circadian process.

    The two-process model:
    - Process S (Sleep Pressure): Builds up during wake, dissipates during sleep
    - Process C (Circadian): 24-hour rhythm with peaks and troughs
    """

    # Circadian rhythm parameters (based on research averages)
    CIRCADIAN_AMPLITUDE = 0.30  # Strength of circadian influence
    CIRCADIAN_PEAK_HOUR = 10.0  # Peak alertness around 10 AM
    CIRCADIAN_TROUGH_HOUR = 3.0  # Lowest alertness around 3 AM
    POST_LUNCH_DIP_HOUR = 14.5  # Afternoon dip around 2:30 PM
    POST_LUNCH_DIP_MAGNITUDE = 0.15

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

    def calculate_circadian_phase(self, hour: float) -> float:
        """
        Calculate circadian alertness factor for a given hour (0-24).

        Uses a modified sinusoidal function with afternoon dip.

        Args:
            hour: Hour of day (0-23.99)

        Returns:
            Circadian factor (0.0-1.0), where 1.0 is peak alertness
        """
        # Base circadian rhythm (sinusoidal with 24-hour period)
        # Phase shift so peak is around 10 AM
        phase_shift = (self.CIRCADIAN_PEAK_HOUR - 6) / 24 * 2 * np.pi
        base_rhythm = np.sin(2 * np.pi * hour / 24 - phase_shift)

        # Normalize to 0-1 range
        circadian_factor = (base_rhythm + 1) / 2

        # Add afternoon dip (post-lunch decrease in alertness)
        afternoon_dip = self._calculate_afternoon_dip(hour)
        circadian_factor = max(0.0, circadian_factor - afternoon_dip)

        # Scale by amplitude
        circadian_factor = 0.5 + (circadian_factor - 0.5) * (1 + self.CIRCADIAN_AMPLITUDE)

        return np.clip(circadian_factor, 0.0, 1.0)

    def _calculate_afternoon_dip(self, hour: float) -> float:
        """Calculate the afternoon dip in alertness (2-4 PM)."""
        # Gaussian curve centered around post-lunch dip time
        dip_center = self.POST_LUNCH_DIP_HOUR
        dip_width = 2.0  # Hours of influence

        dip = self.POST_LUNCH_DIP_MAGNITUDE * np.exp(
            -((hour - dip_center) ** 2) / (2 * dip_width ** 2)
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

        Combines circadian rhythm and sleep pressure.

        Args:
            hour: Hour of day (0-23.99)
            wake_time: Actual wake time
            sleep_hours: Hours of sleep obtained

        Returns:
            Alertness score (0.0-1.0)
        """
        circadian = self.calculate_circadian_phase(hour)
        pressure = self.calculate_sleep_pressure(hour, wake_time, sleep_hours)

        # Alertness is circadian boost minus sleep pressure
        alertness = circadian * (1.0 - pressure * 0.7)

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
