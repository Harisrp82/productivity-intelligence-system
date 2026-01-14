"""
Main automation script for daily productivity intelligence workflow.

This script orchestrates the complete daily workflow:
1. Collect wellness data from Intervals.icu
2. Calculate productivity scores
3. Generate AI insights
4. Store results in database
5. Deliver report to Google Docs

Run this script daily (e.g., via cron at 6 AM).
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_collection import IntervalsICUCollector
from scoring import ProductivityCalculator
from ai import InsightGenerator
from database import DatabaseConnection, WellnessRecord, ProductivityScore, DailyReport
from delivery import GoogleDocsClient


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DailyWorkflow:
    """Orchestrates the complete daily productivity intelligence workflow."""

    def __init__(self):
        """Initialize workflow with configuration from environment variables."""
        load_dotenv()

        # Load configuration
        self.intervals_api_key = os.getenv('INTERVALS_API_KEY')
        self.intervals_athlete_id = os.getenv('INTERVALS_ATHLETE_ID')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_doc_id = os.getenv('GOOGLE_DOC_ID')
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///productivity.db')
        self.timezone = os.getenv('TIMEZONE', 'UTC')

        # Validate configuration
        self._validate_config()

        # Initialize components
        self.collector = IntervalsICUCollector(self.intervals_api_key, self.intervals_athlete_id)
        self.calculator = ProductivityCalculator()
        self.insight_generator = InsightGenerator(self.anthropic_api_key)
        self.db = DatabaseConnection(self.database_url)
        self.google_docs = GoogleDocsClient()

        logger.info("Daily workflow initialized")

    def _validate_config(self):
        """Validate required environment variables."""
        required_vars = [
            'INTERVALS_API_KEY',
            'INTERVALS_ATHLETE_ID',
            'ANTHROPIC_API_KEY',
            'GOOGLE_DOC_ID'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def run(self, date: datetime = None):
        """
        Run the complete daily workflow.

        Args:
            date: Date to process (defaults to yesterday for morning runs)
        """
        # Default to yesterday (for 6 AM runs processing previous day)
        if date is None:
            tz = pytz.timezone(self.timezone)
            now = datetime.now(tz)
            date = (now - timedelta(days=1)).date()
        else:
            date = date.date() if isinstance(date, datetime) else date

        date_str = date.strftime('%Y-%m-%d')
        logger.info(f"Starting daily workflow for {date_str}")

        try:
            # Step 1: Collect data
            logger.info("Step 1: Collecting wellness data")
            daily_data = self.collector.collect_daily_data(datetime.combine(date, datetime.min.time()))

            if not daily_data['wellness']:
                logger.error(f"No wellness data available for {date_str}")
                return False

            # Step 2: Calculate productivity scores
            logger.info("Step 2: Calculating productivity scores")
            productivity_results = self.calculator.calculate_hourly_scores(
                wellness_data=daily_data['wellness'],
                baseline_data=daily_data['baseline']
            )

            # Calculate time blocks
            time_blocks = self.calculator.get_time_block_recommendations(
                productivity_results['hourly_scores']
            )

            # Step 3: Store data in database
            logger.info("Step 3: Storing data in database")
            wellness_record = self._store_wellness_data(date_str, daily_data, productivity_results)

            # Step 4: Generate AI insights
            logger.info("Step 4: Generating AI insights")
            complete_data = {
                'date': date_str,
                'wellness': daily_data['wellness'],
                'baseline': daily_data['baseline'],
                'productivity': productivity_results,
                'time_blocks': time_blocks,
                'recent_activities': daily_data.get('recent_activities', [])
            }

            report_text = self.insight_generator.generate_daily_report(complete_data)

            # Step 5: Store report in database
            logger.info("Step 5: Storing report in database")
            self._store_report(wellness_record.id, date_str, report_text, productivity_results, time_blocks)

            # Step 6: Deliver to Google Docs
            logger.info("Step 6: Delivering report to Google Docs")
            self._deliver_report(date_str, report_text)

            logger.info(f"Daily workflow completed successfully for {date_str}")
            return True

        except Exception as e:
            logger.error(f"Error in daily workflow: {e}", exc_info=True)
            return False

    def _store_wellness_data(self, date_str: str, daily_data: dict,
                            productivity_results: dict) -> WellnessRecord:
        """Store wellness data and productivity scores in database."""
        wellness = daily_data['wellness']
        baseline = daily_data['baseline']

        with self.db.get_session() as session:
            # Check if record already exists
            existing = session.query(WellnessRecord).filter_by(date=date_str).first()

            if existing:
                logger.info(f"Updating existing wellness record for {date_str}")
                record = existing
            else:
                logger.info(f"Creating new wellness record for {date_str}")
                record = WellnessRecord(date=date_str)
                session.add(record)

            # Update wellness data
            record.sleep_seconds = wellness.get('sleep_seconds')
            record.sleep_hours = wellness.get('sleep_hours')
            record.sleep_quality = wellness.get('sleep_quality')
            record.sleep_start = wellness.get('sleep_start')
            record.sleep_end = wellness.get('sleep_end')
            record.resting_hr = wellness.get('resting_hr')
            record.hrv_rmssd = wellness.get('hrv_rmssd')
            record.baseline_hrv = baseline.get('avg_hrv')
            record.baseline_rhr = baseline.get('avg_rhr')
            record.baseline_sleep = baseline.get('avg_sleep_hours')
            record.mood = wellness.get('mood')
            record.fatigue = wellness.get('fatigue')
            record.stress = wellness.get('stress')
            record.soreness = wellness.get('soreness')
            record.weight = wellness.get('weight')

            session.flush()  # Get the ID

            # Store productivity scores
            # Delete existing scores if updating
            if existing:
                session.query(ProductivityScore).filter_by(
                    wellness_record_id=record.id
                ).delete()

            for hour_data in productivity_results['hourly_scores']:
                score = ProductivityScore(
                    wellness_record_id=record.id,
                    hour=hour_data['hour'],
                    score=hour_data['score'],
                    circadian_component=hour_data['circadian_component'],
                    recovery_component=hour_data['recovery_component']
                )
                session.add(score)

            session.commit()
            logger.info(f"Stored wellness data and {len(productivity_results['hourly_scores'])} hourly scores")

            return record

    def _store_report(self, wellness_record_id: int, date_str: str, report_text: str,
                     productivity_results: dict, time_blocks: list):
        """Store generated report in database."""
        with self.db.get_session() as session:
            # Check if report already exists
            existing = session.query(DailyReport).filter_by(
                wellness_record_id=wellness_record_id
            ).first()

            if existing:
                logger.info(f"Updating existing report for {date_str}")
                report = existing
            else:
                logger.info(f"Creating new report for {date_str}")
                report = DailyReport(
                    wellness_record_id=wellness_record_id,
                    date=date_str
                )
                session.add(report)

            # Update report data
            report.full_report = report_text
            report.recovery_score = productivity_results.get('recovery_score')
            report.recovery_status = productivity_results.get('recovery_status')
            report.average_productivity = productivity_results.get('average_score')
            report.peak_hours = [
                {'hour': h['hour'], 'score': h['score']}
                for h in productivity_results.get('peak_hours', [])
            ]
            report.time_blocks = time_blocks

            session.commit()
            logger.info(f"Stored report for {date_str}")

    def _deliver_report(self, date_str: str, report_text: str):
        """Deliver report to Google Docs."""
        # Authenticate
        if not self.google_docs.authenticate():
            logger.error("Failed to authenticate with Google Docs")
            raise Exception("Google Docs authentication failed")

        # Post report
        success = self.google_docs.post_daily_report(
            document_id=self.google_doc_id,
            report_text=report_text,
            date_str=date_str
        )

        if success:
            logger.info(f"Successfully delivered report to Google Docs")

            # Update delivery status in database
            with self.db.get_session() as session:
                report = session.query(DailyReport).filter_by(date=date_str).first()
                if report:
                    report.delivery_status = 'delivered'
                    report.delivered_at = datetime.utcnow()
                    report.google_doc_id = self.google_doc_id
                    session.commit()
        else:
            logger.error("Failed to deliver report to Google Docs")
            raise Exception("Google Docs delivery failed")


def main():
    """Main entry point for daily workflow script."""
    logger.info("=" * 80)
    logger.info("Starting Productivity Intelligence System - Daily Workflow")
    logger.info("=" * 80)

    try:
        workflow = DailyWorkflow()
        success = workflow.run()

        if success:
            logger.info("Workflow completed successfully!")
            sys.exit(0)
        else:
            logger.error("Workflow failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error in workflow: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
