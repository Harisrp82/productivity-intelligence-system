"""
View stored productivity data from the database.

Useful for checking what data has been collected and reviewing past scores.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseConnection, WellnessRecord, ProductivityScore, DailyReport
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def view_recent_records(db: DatabaseConnection, days: int = 7):
    """View recent wellness records."""
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Recent Wellness Records (last {days} days)")
    logger.info('=' * 80)

    with db.get_session() as session:
        # Get recent records
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        records = session.query(WellnessRecord).filter(
            WellnessRecord.date >= cutoff_date
        ).order_by(WellnessRecord.date.desc()).all()

        if not records:
            logger.info("No records found in database.")
            return

        for record in records:
            logger.info(f"\nDate: {record.date}")
            logger.info(f"  Sleep: {record.sleep_hours:.1f}h" if record.sleep_hours else "  Sleep: N/A")
            logger.info(f"  HRV: {record.hrv_rmssd:.1f}ms (baseline: {record.baseline_hrv:.1f}ms)"
                       if record.hrv_rmssd and record.baseline_hrv else "  HRV: N/A")
            logger.info(f"  RHR: {record.resting_hr:.0f}bpm (baseline: {record.baseline_rhr:.0f}bpm)"
                       if record.resting_hr and record.baseline_rhr else "  RHR: N/A")

            # Get report if exists
            if record.daily_report:
                report = record.daily_report
                logger.info(f"  Recovery: {report.recovery_score:.0f}/100 ({report.recovery_status})")
                logger.info(f"  Avg Productivity: {report.average_productivity:.0f}/100")
                logger.info(f"  Report Status: {report.delivery_status}")


def view_date_details(db: DatabaseConnection, date_str: str):
    """View detailed data for a specific date."""
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Detailed Report for {date_str}")
    logger.info('=' * 80)

    with db.get_session() as session:
        record = session.query(WellnessRecord).filter_by(date=date_str).first()

        if not record:
            logger.info(f"No data found for {date_str}")
            return

        # Wellness data
        logger.info("\nWELLNESS METRICS:")
        logger.info(f"  Sleep: {record.sleep_hours:.1f}h" if record.sleep_hours else "  Sleep: N/A")
        logger.info(f"  Quality: {record.sleep_quality}/5" if record.sleep_quality else "  Quality: N/A")
        logger.info(f"  HRV: {record.hrv_rmssd:.1f}ms" if record.hrv_rmssd else "  HRV: N/A")
        logger.info(f"  RHR: {record.resting_hr:.0f}bpm" if record.resting_hr else "  RHR: N/A")

        # Baselines
        if record.baseline_hrv or record.baseline_rhr:
            logger.info("\nBASELINE COMPARISON:")
            if record.hrv_rmssd and record.baseline_hrv:
                diff = record.hrv_rmssd - record.baseline_hrv
                logger.info(f"  HRV: {diff:+.1f}ms from baseline")
            if record.resting_hr and record.baseline_rhr:
                diff = record.resting_hr - record.baseline_rhr
                logger.info(f"  RHR: {diff:+.0f}bpm from baseline")

        # Productivity scores
        if record.productivity_scores:
            logger.info("\nPRODUCTIVITY SCORES:")

            scores = sorted(record.productivity_scores, key=lambda x: x.hour)

            # Show peak hours
            peak_scores = sorted(scores, key=lambda x: x.score, reverse=True)[:5]
            logger.info("  Peak Hours:")
            for score in peak_scores:
                logger.info(f"    {score.hour:02d}:00 - {score.score:.0f}/100")

            # Show all hours
            logger.info("\n  All Hours:")
            for i in range(0, 24, 6):
                hour_scores = scores[i:i+6]
                score_strs = [f"{s.hour:02d}:{s.score:4.0f}" for s in hour_scores]
                logger.info(f"    {' | '.join(score_strs)}")

        # Report
        if record.daily_report:
            report = record.daily_report
            logger.info("\nREPORT SUMMARY:")
            logger.info(f"  Recovery: {report.recovery_score:.0f}/100 ({report.recovery_status})")
            logger.info(f"  Avg Productivity: {report.average_productivity:.0f}/100")
            logger.info(f"  Delivered: {report.delivery_status}")

            if report.time_blocks:
                logger.info("\n  Recommended Focus Blocks:")
                for block in report.time_blocks[:3]:
                    logger.info(f"    - {block['time_window']} (Score: {block['avg_score']:.0f})")


def view_stats(db: DatabaseConnection):
    """View overall database statistics."""
    logger.info(f"\n{'=' * 80}")
    logger.info("Database Statistics")
    logger.info('=' * 80)

    with db.get_session() as session:
        total_records = session.query(WellnessRecord).count()
        total_reports = session.query(DailyReport).count()
        delivered_reports = session.query(DailyReport).filter_by(
            delivery_status='delivered'
        ).count()

        logger.info(f"\nTotal wellness records: {total_records}")
        logger.info(f"Total reports generated: {total_reports}")
        logger.info(f"Successfully delivered: {delivered_reports}")

        if total_records > 0:
            # Date range
            first_record = session.query(WellnessRecord).order_by(
                WellnessRecord.date.asc()
            ).first()
            last_record = session.query(WellnessRecord).order_by(
                WellnessRecord.date.desc()
            ).first()

            logger.info(f"\nDate range: {first_record.date} to {last_record.date}")

            # Average metrics
            records = session.query(WellnessRecord).all()

            avg_sleep = sum(r.sleep_hours for r in records if r.sleep_hours) / len([r for r in records if r.sleep_hours])
            avg_hrv = sum(r.hrv_rmssd for r in records if r.hrv_rmssd) / len([r for r in records if r.hrv_rmssd])
            avg_rhr = sum(r.resting_hr for r in records if r.resting_hr) / len([r for r in records if r.resting_hr])

            logger.info(f"\nAverage Metrics:")
            logger.info(f"  Sleep: {avg_sleep:.1f} hours")
            logger.info(f"  HRV: {avg_hrv:.1f}ms")
            logger.info(f"  RHR: {avg_rhr:.0f}bpm")


def main():
    """Main entry point."""
    load_dotenv()

    db = DatabaseConnection(os.getenv('DATABASE_URL', 'sqlite:///productivity.db'))

    if len(sys.argv) > 1:
        # View specific date
        date_str = sys.argv[1]
        try:
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
            view_date_details(db, date_str)
        except ValueError:
            logger.error(f"Invalid date format: {date_str}")
            logger.info("Use format: YYYY-MM-DD")
            sys.exit(1)
    else:
        # View stats and recent records
        view_stats(db)
        view_recent_records(db, days=7)

        logger.info("\n" + "=" * 80)
        logger.info("To view details for a specific date, run:")
        logger.info("  python scripts/view_data.py YYYY-MM-DD")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
