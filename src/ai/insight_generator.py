"""
Orchestrates AI insight generation using Grok API.
"""

from typing import Dict, Optional
import logging
import json
import re

from .grok_client import GrokClient
from .prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class InsightGenerator:
    """Generates personalized insights from productivity and wellness data."""

    def __init__(self, grok_api_key: str):
        """
        Initialize insight generator.

        Args:
            grok_api_key: xAI Grok API key
        """
        self.grok_client = GrokClient(grok_api_key)
        self.templates = PromptTemplates()

        logger.info("Insight generator initialized with Grok")

    def generate_daily_report(self, complete_data: Dict) -> str:
        """
        Generate complete daily productivity report with AI insights.

        Args:
            complete_data: Dict containing all daily data:
                - date: Date string
                - wellness: Wellness metrics
                - baseline: Baseline averages
                - productivity: Productivity scores and analysis
                - time_blocks: Recommended focus blocks
                - recent_activities: Recent workout data

        Returns:
            Formatted report text ready for Google Docs
        """
        logger.info("Generating daily report with AI insights")

        try:
            # Generate AI insights using Grok
            insight_text = self.grok_client.generate_structured_report(
                system_prompt=self.templates.DAILY_INSIGHT_SYSTEM_PROMPT,
                data=complete_data,
                max_tokens=2000
            )

            # Format into final report
            date_str = complete_data.get('date', 'Unknown Date')
            final_report = self.templates.format_report_for_docs(
                insight_text=insight_text,
                data=complete_data,
                date_str=date_str
            )

            logger.info("Daily report generated successfully")
            return final_report

        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            raise

    def generate_recovery_guidance(self, wellness_data: Dict, baseline_data: Dict,
                                  recovery_results: Dict) -> str:
        """
        Generate focused recovery and intensity guidance.

        Args:
            wellness_data: Today's wellness metrics
            baseline_data: Baseline averages
            recovery_results: Recovery analysis results

        Returns:
            Recovery guidance text
        """
        logger.info("Generating recovery guidance")

        try:
            # Build recovery-focused prompt
            user_prompt = f"""Analyze these recovery metrics and provide guidance:

Recovery Score: {recovery_results.get('overall_score', 0) * 100:.0f}/100
Status: {recovery_results.get('status', 'unknown')}

HRV: {wellness_data.get('hrv_rmssd', 'N/A')} ms (baseline: {baseline_data.get('avg_hrv', 'N/A')} ms)
RHR: {wellness_data.get('resting_hr', 'N/A')} bpm (baseline: {baseline_data.get('avg_rhr', 'N/A')} bpm)
Sleep: {wellness_data.get('sleep_hours', 'N/A')} hours

Provide specific guidance on:
1. Today's optimal training/work intensity
2. Recovery strategies if needed
3. Warning signs to watch for"""

            insight = self.grok_client.generate_insight(
                system_prompt=self.templates.RECOVERY_ANALYSIS_PROMPT,
                user_prompt=user_prompt,
                max_tokens=800
            )

            logger.info("Recovery guidance generated")
            return insight

        except Exception as e:
            logger.error(f"Error generating recovery guidance: {e}")
            raise

    def generate_schedule_optimization(self, hourly_scores: list) -> str:
        """
        Generate time block and schedule optimization recommendations.

        Args:
            hourly_scores: List of hourly productivity scores

        Returns:
            Schedule optimization text
        """
        logger.info("Generating schedule optimization")

        try:
            user_prompt = self.templates.get_time_block_optimization_prompt(hourly_scores)

            insight = self.grok_client.generate_insight(
                system_prompt=self.templates.DAILY_INSIGHT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=1000
            )

            logger.info("Schedule optimization generated")
            return insight

        except Exception as e:
            logger.error(f"Error generating schedule optimization: {e}")
            raise

    def generate_quick_summary(self, complete_data: Dict) -> str:
        """
        Generate a brief summary for quick consumption (e.g., notifications).

        Args:
            complete_data: Complete daily data

        Returns:
            Brief summary text (< 100 words)
        """
        productivity = complete_data.get('productivity', {})
        wellness = complete_data.get('wellness', {})

        recovery_status = productivity.get('recovery_status', 'unknown')
        recovery_score = productivity.get('recovery_score', 0)
        avg_productivity = productivity.get('average_score', 0)
        sleep_hours = wellness.get('sleep_hours', 0)

        peak_hours = productivity.get('peak_hours', [])
        peak_times = [f"{h['hour']:02d}:00" for h in peak_hours[:3]]

        summary = f"""Recovery: {recovery_status.title()} ({recovery_score:.0f}/100)
Sleep: {sleep_hours:.1f}h
Avg Productivity: {avg_productivity:.0f}/100

Peak hours: {', '.join(peak_times)}

Focus on deep work during peak windows and adjust intensity based on {recovery_status} recovery."""

        return summary

    def generate_deep_work_windows(self, complete_data: Dict) -> Optional[Dict]:
        """
        Generate optimal deep work windows using LLM analysis.

        Args:
            complete_data: Dict containing all daily data:
                - wellness: Wellness metrics (sleep, HR, etc.)
                - productivity: Productivity scores and hourly data

        Returns:
            Dict with deep work window recommendations or None if failed
        """
        logger.info("Generating deep work windows with AI analysis")

        try:
            # Build the prompt with data
            user_prompt = self.templates.get_deep_work_window_prompt(complete_data)

            # Call LLM for analysis
            response = self.grok_client.generate_insight(
                system_prompt=self.templates.DEEP_WORK_WINDOW_PROMPT,
                user_prompt=user_prompt,
                max_tokens=1000
            )

            # Parse JSON response
            deep_work_data = self._parse_deep_work_response(response)

            if deep_work_data:
                logger.info(f"Deep work analysis complete: {deep_work_data.get('summary', 'No summary')}")
                return deep_work_data
            else:
                logger.warning("Failed to parse deep work response, returning raw")
                return {'raw_response': response}

        except Exception as e:
            logger.error(f"Error generating deep work windows: {e}")
            return None

    def _parse_deep_work_response(self, response: str) -> Optional[Dict]:
        """
        Parse the LLM response to extract structured deep work data.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed dict or None if parsing fails
        """
        try:
            # Try to find JSON in the response
            # Look for JSON block between curly braces
            json_match = re.search(r'\{[\s\S]*\}', response)

            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)

            # If no JSON found, try parsing the whole response
            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse deep work JSON: {e}")
            return None
