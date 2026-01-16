"""
Sleep debt calculation with exponential decay model.

Sleep debt represents the cumulative deficit between actual sleep and personal
sleep needs, with older debt decaying over time.
"""

import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SleepDebtCalculator:
    """
    Calculates cumulative sleep debt using exponential decay model.

    Model: Debt(today) = (Debt(yesterday) * decay_factor) + (Need - Actual)

    Parameters:
        - decay_factor: 0.85 (15% decay per day)
        - max_debt: 40 hours (physiological ceiling)
        - default_sleep_need: 8 hours (if baseline unavailable)
    """

    # Model parameters
    DECAY_FACTOR = 0.85          # 15% daily decay
    MAX_DEBT = 40.0              # Maximum accumulated debt (hours)
    MIN_DEBT = 0.0               # Minimum debt (cannot go negative)
    DEFAULT_SLEEP_NEED = 8.0     # Default if baseline unavailable

    # Recovery thresholds for categorization
    DEBT_LOW_THRESHOLD = 5.0        # < 5 hours = low debt
    DEBT_MODERATE_THRESHOLD = 15.0  # 5-15 hours = moderate
    DEBT_HIGH_THRESHOLD = 25.0      # 15-25 hours = high
    # > 25 hours = severe

    def __init__(self):
        """Initialize sleep debt calculator."""
        logger.info("Sleep debt calculator initialized")

    def calculate_daily_debt(
        self,
        previous_debt: Optional[float],
        actual_sleep: Optional[float],
        sleep_need: Optional[float]
    ) -> float:
        """
        Calculate today's sleep debt based on previous debt and last night's sleep.

        Args:
            previous_debt: Yesterday's accumulated sleep debt (hours), None if first day
            actual_sleep: Last night's actual sleep duration (hours)
            sleep_need: Personal sleep need (from baseline_sleep or default)

        Returns:
            Today's accumulated sleep debt (hours)
        """
        # Handle None values gracefully
        if previous_debt is None:
            previous_debt = 0.0
            logger.info("No previous debt, starting from 0")

        if actual_sleep is None:
            logger.warning("No sleep data available, maintaining previous debt with decay")
            # Still apply decay even without new data
            return round(np.clip(previous_debt * self.DECAY_FACTOR, self.MIN_DEBT, self.MAX_DEBT), 2)

        if sleep_need is None:
            sleep_need = self.DEFAULT_SLEEP_NEED
            logger.info(f"Using default sleep need: {sleep_need} hours")

        # Apply decay to previous debt
        decayed_debt = previous_debt * self.DECAY_FACTOR

        # Calculate today's deficit/surplus
        daily_deficit = sleep_need - actual_sleep

        # Accumulate new debt
        new_debt = decayed_debt + daily_deficit

        # Clamp to valid range (0 to MAX_DEBT)
        new_debt = np.clip(new_debt, self.MIN_DEBT, self.MAX_DEBT)

        logger.debug(
            f"Sleep debt: {previous_debt:.1f} -> {new_debt:.1f} "
            f"(slept {actual_sleep:.1f}h, need {sleep_need:.1f}h)"
        )

        return round(float(new_debt), 2)

    def get_debt_category(self, debt: Optional[float]) -> str:
        """
        Categorize sleep debt level.

        Args:
            debt: Current sleep debt in hours

        Returns:
            Category string: 'none', 'low', 'moderate', 'high', 'severe'
        """
        if debt is None:
            return 'unknown'

        if debt < 1.0:
            return 'none'
        elif debt < self.DEBT_LOW_THRESHOLD:
            return 'low'
        elif debt < self.DEBT_MODERATE_THRESHOLD:
            return 'moderate'
        elif debt < self.DEBT_HIGH_THRESHOLD:
            return 'high'
        else:
            return 'severe'

    def calculate_debt_impact_factor(self, debt: Optional[float]) -> float:
        """
        Calculate recovery impact factor based on sleep debt.

        Higher debt = lower recovery capacity = lower factor.

        Args:
            debt: Current sleep debt in hours

        Returns:
            Impact factor (0.5-1.0) where 1.0 is no impact
        """
        if debt is None:
            return 1.0  # No impact if unknown

        # Linear decay from 1.0 (no debt) to 0.5 (max debt)
        # Formula: 1.0 - (debt / MAX_DEBT) * 0.5
        impact = 1.0 - (debt / self.MAX_DEBT) * 0.5

        return float(np.clip(impact, 0.5, 1.0))

    def estimate_recovery_days(self, debt: Optional[float], sleep_surplus: float = 1.0) -> int:
        """
        Estimate days needed to fully recover from sleep debt.

        Assumes consistent sleep surplus each day.

        Args:
            debt: Current sleep debt in hours
            sleep_surplus: Expected daily sleep surplus (hours above need)

        Returns:
            Estimated days to full recovery
        """
        if debt is None or debt < 1.0:
            return 0

        # Simulate debt reduction day by day
        days = 0
        current_debt = debt

        while current_debt >= 1.0 and days < 30:  # Max 30 days
            current_debt = current_debt * self.DECAY_FACTOR - sleep_surplus
            current_debt = max(0, current_debt)
            days += 1

        return days

    def get_debt_insights(
        self,
        debt: Optional[float],
        actual_sleep: Optional[float],
        sleep_need: Optional[float]
    ) -> List[str]:
        """
        Generate human-readable insights about sleep debt.

        Args:
            debt: Current accumulated sleep debt
            actual_sleep: Last night's sleep
            sleep_need: Personal sleep need

        Returns:
            List of insight strings
        """
        insights = []

        if debt is None:
            return ["Sleep debt data not available."]

        if sleep_need is None:
            sleep_need = self.DEFAULT_SLEEP_NEED

        category = self.get_debt_category(debt)

        # Category-based insights
        category_messages = {
            'none': "You have no significant sleep debt. Your sleep is well-balanced.",
            'low': f"Mild sleep debt of {debt:.1f} hours. A few good nights will clear this.",
            'moderate': f"Moderate sleep debt of {debt:.1f} hours. Consider prioritizing sleep this week.",
            'high': f"Significant sleep debt of {debt:.1f} hours. This may be affecting your cognitive performance.",
            'severe': f"Severe sleep debt of {debt:.1f} hours. Recovery should be a top priority."
        }
        insights.append(category_messages.get(category, "Sleep debt status unknown."))

        # Deficit/surplus insight for last night
        if actual_sleep is not None:
            daily_change = sleep_need - actual_sleep
            if daily_change > 0.5:
                insights.append(
                    f"Last night you were {daily_change:.1f}h short of your need, adding to your debt."
                )
            elif daily_change < -0.5:
                insights.append(
                    f"Last night you got {abs(daily_change):.1f}h extra sleep, helping reduce your debt."
                )

        # Recovery estimate for significant debt
        if debt >= self.DEBT_LOW_THRESHOLD:
            recovery_days = self.estimate_recovery_days(debt)
            insights.append(
                f"Estimated {recovery_days} days to full recovery with consistent extra sleep."
            )

        return insights
