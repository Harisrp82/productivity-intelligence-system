"""
Prompt templates for Claude AI insight generation.
"""


class PromptTemplates:
    """Collection of system and user prompts for different insight types."""

    DAILY_INSIGHT_SYSTEM_PROMPT = """You are an expert productivity coach and sleep scientist specializing in circadian biology, recovery physiology, and performance optimization.

Your role is to analyze wellness data (sleep, HRV, heart rate) and productivity scores to generate personalized, actionable insights for the user's day.

Guidelines:
1. Be direct and actionable - focus on specific recommendations
2. Use scientific principles (circadian rhythm, recovery physiology) but explain in accessible language
3. Prioritize the top 2-3 most important insights
4. Format recommendations as clear action items
5. Acknowledge both strengths and opportunities for optimization
6. Be honest about limitations (e.g., if recovery is poor, say so)
7. Keep the total response under 500 words

Structure your response in these sections:
- **Recovery Summary**: 1-2 sentences on overall physiological state
- **Today's Optimal Windows**: Best times for focused work
- **Energy Management**: How to work with your natural rhythms
- **Recommendations**: 2-3 specific action items for today

Use a professional but encouraging tone. Avoid unnecessary jargon."""

    WEEKLY_SUMMARY_SYSTEM_PROMPT = """You are an expert in sleep science and productivity optimization.

Analyze a week's worth of wellness and productivity data to identify patterns, trends, and opportunities for improvement.

Guidelines:
1. Focus on patterns across the week, not individual days
2. Identify correlations (e.g., HRV trends vs productivity)
3. Highlight what's working well
4. Suggest 1-2 strategic improvements for next week
5. Be data-driven but practical
6. Keep response under 400 words

Structure:
- **Week Overview**: Overall patterns and trends
- **Strengths**: What went well
- **Opportunities**: Areas for improvement
- **Next Week Focus**: 1-2 specific goals"""

    RECOVERY_ANALYSIS_PROMPT = """You are a recovery and performance specialist.

Analyze the user's recovery metrics (HRV, RHR, sleep) and provide specific guidance on training intensity and stress management for today.

Focus on:
1. What the recovery metrics indicate about autonomic nervous system balance
2. Whether today is suitable for high-intensity work/exercise
3. Specific recovery strategies if needed
4. How to adjust plans based on current state

Keep response under 300 words."""

    @staticmethod
    def get_daily_insight_prompt(data: dict) -> str:
        """
        Generate the user prompt for daily insights.

        Args:
            data: Complete daily data (wellness, productivity, activities)

        Returns:
            Formatted user prompt
        """
        return """Please analyze the following data and provide personalized insights for today.

Focus on:
1. How today's recovery metrics compare to baseline
2. The optimal time windows for deep work
3. Practical recommendations for energy management
4. Any red flags or exceptional conditions

Here's the data:

{data}

Generate your daily insight following the structure in your system prompt."""

    @staticmethod
    def get_time_block_optimization_prompt(hourly_scores: list) -> str:
        """
        Generate prompt for optimizing time block allocation.

        Args:
            hourly_scores: List of hourly productivity scores

        Returns:
            Formatted prompt
        """
        # Format scores into readable list
        score_list = []
        for hour_data in hourly_scores:
            hour = hour_data['hour']
            score = hour_data['score']
            score_list.append(f"{hour:02d}:00 - {score:.0f}/100")

        scores_text = "\n".join(score_list)

        return f"""Based on these hourly productivity scores, recommend the optimal schedule structure:

{scores_text}

Provide:
1. Best 2-3 time blocks for deep, focused work
2. Good times for meetings/collaboration
3. Times to avoid for demanding tasks
4. Suggested break/recovery windows

Be specific with time recommendations."""

    @staticmethod
    def format_report_for_docs(insight_text: str, data: dict, date_str: str) -> str:
        """
        Format the final report for Google Docs output.

        Args:
            insight_text: Generated insight from Claude
            data: Complete productivity data
            date_str: Date string for header

        Returns:
            Formatted report text
        """
        productivity = data.get('productivity', {})
        wellness = data.get('wellness', {})

        report_parts = []

        # Header
        report_parts.append(f"# Productivity Intelligence Report")
        report_parts.append(f"## {date_str}")
        report_parts.append("")
        report_parts.append("---")
        report_parts.append("")

        # Key metrics summary
        report_parts.append("### Quick Stats")
        report_parts.append("")
        sleep_hours = wellness.get('sleep_hours')
        sleep_str = f"{sleep_hours:.1f} hours" if sleep_hours is not None else "N/A"
        report_parts.append(f"- **Sleep**: {sleep_str}")
        recovery_score = productivity.get('recovery_score')
        recovery_str = f"{recovery_score}/100" if recovery_score is not None else "N/A"
        report_parts.append(f"- **Recovery Score**: {recovery_str} ({productivity.get('recovery_status', 'unknown')})")
        avg_score = productivity.get('average_score')
        avg_str = f"{avg_score}/100" if avg_score is not None else "N/A"
        report_parts.append(f"- **Avg Productivity**: {avg_str}")
        report_parts.append("")

        # Peak hours
        peak_hours = productivity.get('peak_hours', [])
        if peak_hours:
            report_parts.append("### Peak Productivity Hours")
            report_parts.append("")
            for hour_data in peak_hours[:5]:
                hour = hour_data['hour']
                score = hour_data['score']
                report_parts.append(f"- **{hour:02d}:00** - Score: {score:.0f}/100")
            report_parts.append("")

        # AI insights
        report_parts.append("### AI Insights")
        report_parts.append("")
        report_parts.append(insight_text)
        report_parts.append("")

        # Time blocks
        time_blocks = data.get('time_blocks', [])
        if time_blocks:
            report_parts.append("---")
            report_parts.append("")
            report_parts.append("### Recommended Focus Blocks")
            report_parts.append("")
            for i, block in enumerate(time_blocks[:3], 1):
                report_parts.append(f"{i}. **{block['time_window']}** - {block['duration_hours']} hours (Score: {block['avg_score']:.0f})")
            report_parts.append("")

        # Footer
        report_parts.append("---")
        report_parts.append("")
        report_parts.append(f"*Generated automatically by Productivity Intelligence System*")
        report_parts.append(f"*Powered by Grok AI and Intervals.icu data*")

        return "\n".join(report_parts)
