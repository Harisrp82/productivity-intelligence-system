"""
Test the complete workflow end-to-end without posting to Google Docs.

Useful for testing all components before going live.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection import IntervalsICUCollector
from src.scoring import ProductivityCalculator
from src.ai import InsightGenerator
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test complete workflow without database or Google Docs."""
    logger.info("=" * 80)
    logger.info("Testing Complete Workflow (Dry Run)")
    logger.info("=" * 80)

    # Load environment
    load_dotenv()

    # Initialize components
    logger.info("\nInitializing components...")

    collector = IntervalsICUCollector(
        api_key=os.getenv('INTERVALS_API_KEY'),
        athlete_id=os.getenv('INTERVALS_ATHLETE_ID')
    )

    calculator = ProductivityCalculator()

    insight_generator = InsightGenerator(
        claude_api_key=os.getenv('ANTHROPIC_API_KEY')
    )

    # Use yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')

    # Step 1: Collect data
    logger.info("\n" + "=" * 80)
    logger.info(f"Step 1: Collecting data for {date_str}")
    logger.info("=" * 80)

    daily_data = collector.collect_daily_data(yesterday)

    if not daily_data['wellness']:
        logger.error("No wellness data available!")
        return False

    logger.info("Data collected successfully!")
    logger.info(f"  Sleep: {daily_data['wellness']['sleep_hours']:.1f} hours")
    logger.info(f"  HRV: {daily_data['wellness'].get('hrv_rmssd', 'N/A')} ms")
    logger.info(f"  RHR: {daily_data['wellness'].get('resting_hr', 'N/A')} bpm")

    # Step 2: Calculate productivity scores
    logger.info("\n" + "=" * 80)
    logger.info("Step 2: Calculating productivity scores")
    logger.info("=" * 80)

    productivity_results = calculator.calculate_hourly_scores(
        wellness_data=daily_data['wellness'],
        baseline_data=daily_data['baseline']
    )

    logger.info("Productivity scores calculated!")
    logger.info(f"  Recovery: {productivity_results['recovery_score']}/100 ({productivity_results['recovery_status']})")
    logger.info(f"  Average Score: {productivity_results['average_score']}/100")
    logger.info(f"  Peak Hours:")
    for hour_data in productivity_results['peak_hours'][:3]:
        logger.info(f"    - {hour_data['hour']:02d}:00 (Score: {hour_data['score']:.0f})")

    # Calculate time blocks
    time_blocks = calculator.get_time_block_recommendations(
        productivity_results['hourly_scores']
    )

    logger.info(f"  Optimal Focus Blocks: {len(time_blocks)}")
    for i, block in enumerate(time_blocks[:3], 1):
        logger.info(f"    {i}. {block['time_window']} (Score: {block['avg_score']:.0f})")

    # Step 3: Generate AI insights
    logger.info("\n" + "=" * 80)
    logger.info("Step 3: Generating AI insights with Claude")
    logger.info("=" * 80)

    complete_data = {
        'date': date_str,
        'wellness': daily_data['wellness'],
        'baseline': daily_data['baseline'],
        'productivity': productivity_results,
        'time_blocks': time_blocks,
        'recent_activities': daily_data.get('recent_activities', [])
    }

    report_text = insight_generator.generate_daily_report(complete_data)

    logger.info("AI report generated successfully!")
    logger.info(f"Report length: {len(report_text)} characters")

    # Display the report
    logger.info("\n" + "=" * 80)
    logger.info("GENERATED REPORT")
    logger.info("=" * 80)
    print("\n" + report_text + "\n")

    logger.info("=" * 80)
    logger.info("Workflow test completed successfully!")
    logger.info("=" * 80)
    logger.info("\nAll components are working correctly.")
    logger.info("Ready to run the full workflow with:")
    logger.info("  python daily_workflow.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
