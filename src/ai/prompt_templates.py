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

    DEEP_WORK_WINDOW_PROMPT = """You are an expert in chronobiology, cognitive performance, and deep work optimization.

Your task is to analyze the user's physiological data and productivity scores to identify the OPTIMAL deep work windows for today.

Deep work requires:
- Sustained attention and focus (90-120 minute blocks)
- High cognitive energy (aligned with circadian peaks)
- Good recovery status (to support mental stamina)
- Minimal expected interruptions

Guidelines:
1. Identify 1-3 optimal deep work windows based on the data
2. Each window should be at least 90 minutes for meaningful deep work
3. Consider the user's wake time and natural energy patterns
4. Factor in recovery status - if poor recovery, recommend shorter/fewer windows
5. Be SPECIFIC with exact start and end times (e.g., "14:00 - 16:00")
6. Explain WHY each window is optimal based on the data

Response format (use exactly this JSON structure):
{
    "primary_window": {
        "start": "HH:MM",
        "end": "HH:MM",
        "duration_minutes": 120,
        "quality_score": 85,
        "reasoning": "Brief explanation"
    },
    "secondary_window": {
        "start": "HH:MM",
        "end": "HH:MM",
        "duration_minutes": 90,
        "quality_score": 70,
        "reasoning": "Brief explanation"
    },
    "avoid_windows": ["HH:MM - HH:MM", "HH:MM - HH:MM"],
    "daily_deep_work_capacity": "X hours",
    "energy_pattern": "morning_person|evening_person|mixed",
    "summary": "One sentence summary of today's deep work potential"
}

Be realistic and data-driven. If the data suggests limited deep work capacity today, say so honestly."""

    @staticmethod
    def get_deep_work_window_prompt(data: dict) -> str:
        """
        Generate the user prompt for deep work window analysis.

        Args:
            data: Complete daily data (wellness, productivity, hourly_scores)

        Returns:
            Formatted user prompt for deep work analysis
        """
        wellness = data.get('wellness', {})
        productivity = data.get('productivity', {})
        hourly_scores = productivity.get('hourly_scores', [])

        # Format hourly scores
        score_lines = []
        for hour_data in hourly_scores:
            hour = hour_data.get('hour', 0)
            score = hour_data.get('score', 0)
            score_lines.append(f"  {hour:02d}:00 - {score:.0f}/100")
        scores_text = "\n".join(score_lines)

        # Extract key metrics
        sleep_hours = wellness.get('sleep_hours', 'N/A')
        sleep_end = wellness.get('sleep_end', 'N/A')
        resting_hr = wellness.get('resting_hr', 'N/A')
        recovery_score = productivity.get('recovery_score', 'N/A')
        recovery_status = productivity.get('recovery_status', 'unknown')

        return f"""Analyze this data and identify optimal deep work windows for today:

**Recovery Status**
- Recovery Score: {recovery_score}/100 ({recovery_status})
- Sleep Duration: {sleep_hours} hours
- Wake Time: {sleep_end}
- Resting Heart Rate: {resting_hr} bpm

**Hourly Productivity Scores**
{scores_text}

Based on this physiological and productivity data, identify the best deep work windows.
Consider the wake time, recovery status, and hourly score patterns.
Return your analysis in the JSON format specified."""

    @staticmethod
    def get_daily_insight_prompt(data: dict) -> str:
        """
        Generate the user prompt for daily insights.

        Args:
            data: Complete daily data (wellness, productivity, activities)

        Returns:
            Formatted user prompt
        """
        # Extract sleep debt info for explicit inclusion
        sleep_debt = data.get('sleep_debt')
        sleep_debt_category = data.get('sleep_debt_category', 'unknown')
        debt_info = ""
        if sleep_debt is not None:
            debt_info = f"\n\nSleep Debt: {sleep_debt:.1f} hours ({sleep_debt_category})"
            if sleep_debt >= 15:
                debt_info += "\n**Note: Significant sleep debt detected. Factor this into your recommendations.**"

        return f"""Please analyze the following data and provide personalized insights for today.

Focus on:
1. How today's recovery metrics compare to baseline
2. The optimal time windows for deep work
3. Practical recommendations for energy management
4. Any red flags or exceptional conditions
5. Sleep debt impact on today's capacity{debt_info}

Here's the data:

{{data}}

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
        sleep_debt = data.get('sleep_debt')
        debt_str = f"{sleep_debt:.1f} hours" if sleep_debt is not None else "N/A"
        debt_category = data.get('sleep_debt_category', 'unknown')
        report_parts.append(f"- **Sleep Debt**: {debt_str} ({debt_category})")
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

        # Sleep Debt Analysis
        debt_insights = data.get('sleep_debt_insights', [])
        if debt_insights:
            report_parts.append("### Sleep Debt Analysis")
            report_parts.append("")
            for insight in debt_insights:
                report_parts.append(f"- {insight}")
            report_parts.append("")

        # Energy Flow Prediction (based on actual wake time)
        energy_flow = productivity.get('energy_flow', {})
        if energy_flow:
            report_parts.append("### Energy Flow (Adaptive to Wake Time)")
            report_parts.append("")
            report_parts.append(f"**Wake Time**: {energy_flow.get('wake_time', 'N/A')} | **Sleep**: {energy_flow.get('sleep_hours', 'N/A')} hours")
            report_parts.append("")

            # High energy windows
            high_windows = energy_flow.get('high_energy_windows', [])
            if high_windows:
                report_parts.append("**High Energy Windows (Best for Deep Work):**")
                for window in high_windows:
                    report_parts.append(f"- **{window['name']}**: {window['start']} - {window['end']} ({window['hours_after_wake']} after waking)")
                    report_parts.append(f"  - Energy: {window['energy_level']}% | Best for: {window['best_for']}")
                report_parts.append("")

            # Low energy windows
            low_windows = energy_flow.get('low_energy_windows', [])
            if low_windows:
                report_parts.append("**Low Energy Windows (Avoid Deep Work):**")
                for window in low_windows:
                    report_parts.append(f"- **{window['name']}**: {window['start']} - {window['end']} ({window['hours_after_wake']} after waking)")
                    report_parts.append(f"  - Energy: {window['energy_level']}% | Best for: {window['best_for']}")
                report_parts.append("")

            # Summary
            summary = energy_flow.get('summary', '')
            if summary:
                report_parts.append(f"> {summary}")
                report_parts.append("")

        # Deep Work Windows (LLM-generated additional analysis)
        deep_work = data.get('deep_work_windows', {})
        if deep_work and not deep_work.get('raw_response'):
            report_parts.append("### AI Deep Work Recommendations")
            report_parts.append("")

            # Primary window
            primary = deep_work.get('primary_window', {})
            if primary:
                report_parts.append(f"**Primary Window**: {primary.get('start', 'N/A')} - {primary.get('end', 'N/A')}")
                report_parts.append(f"- Duration: {primary.get('duration_minutes', 0)} minutes")
                report_parts.append(f"- Quality Score: {primary.get('quality_score', 0)}/100")
                report_parts.append(f"- *{primary.get('reasoning', '')}*")
                report_parts.append("")

            # Secondary window
            secondary = deep_work.get('secondary_window', {})
            if secondary:
                report_parts.append(f"**Secondary Window**: {secondary.get('start', 'N/A')} - {secondary.get('end', 'N/A')}")
                report_parts.append(f"- Duration: {secondary.get('duration_minutes', 0)} minutes")
                report_parts.append(f"- Quality Score: {secondary.get('quality_score', 0)}/100")
                report_parts.append(f"- *{secondary.get('reasoning', '')}*")
                report_parts.append("")

            # Daily capacity
            capacity = deep_work.get('daily_deep_work_capacity', 'Unknown')
            report_parts.append(f"**Daily Deep Work Capacity**: {capacity}")
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

        return "\n".join(report_parts)
