"""
Groq API client wrapper for generating AI insights.
Uses Groq's API as an alternative to Claude.
"""

import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GrokClient:
    """Wrapper for Groq API."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_MAX_TOKENS = 2000

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key
            model: Model ID to use (defaults to llama-3.3-70b-versatile)
        """
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        logger.info(f"Groq client initialized with model: {self.model}")

    def generate_insight(self, system_prompt: str, user_prompt: str,
                        max_tokens: Optional[int] = None) -> str:
        """
        Generate insight using Grok API.

        Args:
            system_prompt: System instructions for Grok
            user_prompt: User message with data to analyze
            max_tokens: Maximum tokens in response

        Returns:
            Generated insight text
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens or self.DEFAULT_MAX_TOKENS,
                "temperature": 0.7
            }

            response = requests.post(
                self.BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            insight = result['choices'][0]['message']['content']

            logger.info(f"Successfully generated insight ({len(insight)} characters)")
            return insight

        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating insight with Grok: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response content: {e.response.text}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Grok response: {e}")
            raise

    def generate_structured_report(self, system_prompt: str, data: Dict,
                                   max_tokens: Optional[int] = None) -> str:
        """
        Generate a structured report from productivity data.

        Args:
            system_prompt: System instructions
            data: Productivity and wellness data
            max_tokens: Maximum tokens in response

        Returns:
            Formatted report text
        """
        # Format data into a readable prompt
        user_prompt = self._format_data_prompt(data)

        return self.generate_insight(system_prompt, user_prompt, max_tokens)

    def _format_data_prompt(self, data: Dict) -> str:
        """
        Format productivity data into a structured prompt.

        Args:
            data: Complete productivity and wellness data

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # Date and basic info
        prompt_parts.append(f"Date: {data.get('date', 'Unknown')}")
        prompt_parts.append("")

        # Sleep data
        wellness = data.get('wellness', {})
        if wellness:
            prompt_parts.append("SLEEP DATA:")
            prompt_parts.append(f"- Duration: {wellness.get('sleep_hours', 'N/A'):.1f} hours")
            prompt_parts.append(f"- Wake time: {data.get('productivity', {}).get('wake_time', 'N/A')}")
            if wellness.get('sleep_quality'):
                prompt_parts.append(f"- Quality rating: {wellness.get('sleep_quality')}/5")
            prompt_parts.append("")

        # Recovery metrics
        baseline = data.get('baseline', {})
        recovery = data.get('productivity', {})

        if wellness and baseline:
            prompt_parts.append("RECOVERY METRICS:")
            if wellness.get('hrv_rmssd') and baseline.get('avg_hrv'):
                hrv_diff = wellness['hrv_rmssd'] - baseline['avg_hrv']
                prompt_parts.append(f"- HRV: {wellness['hrv_rmssd']:.1f}ms (baseline: {baseline['avg_hrv']:.1f}ms, {hrv_diff:+.1f}ms)")
            if wellness.get('resting_hr') and baseline.get('avg_rhr'):
                rhr_diff = wellness['resting_hr'] - baseline['avg_rhr']
                prompt_parts.append(f"- RHR: {wellness['resting_hr']:.0f} bpm (baseline: {baseline['avg_rhr']:.0f} bpm, {rhr_diff:+.0f} bpm)")
            if recovery.get('recovery_score'):
                prompt_parts.append(f"- Overall recovery: {recovery['recovery_score']}/100 ({recovery.get('recovery_status', 'unknown')})")
            prompt_parts.append("")

        # Productivity scores
        productivity = data.get('productivity', {})
        if productivity:
            prompt_parts.append("PRODUCTIVITY ANALYSIS:")
            prompt_parts.append(f"- Average score: {productivity.get('average_score', 'N/A')}/100")

            peak_hours = productivity.get('peak_hours', [])
            if peak_hours:
                prompt_parts.append("- Peak hours:")
                for hour_data in peak_hours[:3]:
                    hour = hour_data['hour']
                    score = hour_data['score']
                    prompt_parts.append(f"  * {hour:02d}:00 - Score: {score:.0f}")

            low_hours = productivity.get('low_hours', [])
            if low_hours:
                prompt_parts.append("- Low energy hours:")
                for hour_data in low_hours[:2]:
                    hour = hour_data['hour']
                    score = hour_data['score']
                    prompt_parts.append(f"  * {hour:02d}:00 - Score: {score:.0f}")
            prompt_parts.append("")

        # Time blocks
        time_blocks = data.get('time_blocks', [])
        if time_blocks:
            prompt_parts.append("OPTIMAL FOCUS WINDOWS:")
            for i, block in enumerate(time_blocks[:3], 1):
                prompt_parts.append(f"{i}. {block['time_window']} ({block['duration_hours']}h, score: {block['avg_score']:.0f})")
            prompt_parts.append("")

        # Recent activities
        activities = data.get('recent_activities', [])
        if activities:
            prompt_parts.append("RECENT ACTIVITIES (last 3 days):")
            for activity in activities[:3]:
                activity_date = activity.get('start_date', 'Unknown')[:10]
                activity_type = activity.get('type', 'Unknown')
                duration = activity.get('duration', 0) / 60  # Convert to minutes
                prompt_parts.append(f"- {activity_date}: {activity_type} ({duration:.0f} min)")
            prompt_parts.append("")

        return "\n".join(prompt_parts)
