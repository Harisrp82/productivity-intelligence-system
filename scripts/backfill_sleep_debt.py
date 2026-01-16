"""
One-time script to backfill sleep_debt for existing WellnessRecord entries.

Run this script after adding the sleep_debt column to the database:
    ALTER TABLE wellness_records ADD COLUMN sleep_debt FLOAT;

Usage:
    python scripts/backfill_sleep_debt.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import logging
from database import DatabaseConnection, WellnessRecord
from scoring import SleepDebtCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_sleep_debt(dry_run: bool = False):
    """
    Calculate and store sleep debt for all historical records.

    Args:
        dry_run: If True, only print what would be done without making changes
    """
    db = DatabaseConnection()
    calculator = SleepDebtCalculator()

    with db.get_session() as session:
        # Get all records ordered by date (oldest first for correct debt accumulation)
        records = session.query(WellnessRecord).order_by(
            WellnessRecord.date.asc()
        ).all()

        if not records:
            logger.warning("No wellness records found in database")
            return

        logger.info(f"Found {len(records)} records to process")
        logger.info(f"Date range: {records[0].date} to {records[-1].date}")

        if dry_run:
            logger.info("DRY RUN - No changes will be made")

        previous_debt = None
        updated_count = 0
        skipped_count = 0

        for record in records:
            # Use baseline_sleep or default
            sleep_need = record.baseline_sleep or 8.0
            actual_sleep = record.sleep_hours

            if actual_sleep is None:
                logger.warning(f"{record.date}: No sleep data, skipping")
                skipped_count += 1
                # Still carry forward the previous debt with decay
                if previous_debt is not None:
                    previous_debt = calculator.calculate_daily_debt(
                        previous_debt=previous_debt,
                        actual_sleep=None,
                        sleep_need=sleep_need
                    )
                continue

            # Calculate debt
            sleep_debt = calculator.calculate_daily_debt(
                previous_debt=previous_debt,
                actual_sleep=actual_sleep,
                sleep_need=sleep_need
            )

            # Determine daily change for logging
            daily_deficit = sleep_need - actual_sleep
            change_str = f"+{daily_deficit:.1f}h" if daily_deficit > 0 else f"{daily_deficit:.1f}h"

            category = calculator.get_debt_category(sleep_debt)

            logger.info(
                f"{record.date}: slept {actual_sleep:.1f}h (need {sleep_need:.1f}h, {change_str}) "
                f"-> debt: {sleep_debt:.1f}h ({category})"
            )

            if not dry_run:
                record.sleep_debt = sleep_debt

            previous_debt = sleep_debt
            updated_count += 1

        if not dry_run:
            session.commit()
            logger.info(f"Backfill complete. Updated {updated_count} records, skipped {skipped_count}")
        else:
            logger.info(f"DRY RUN complete. Would update {updated_count} records, skip {skipped_count}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Backfill sleep debt for historical records")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Sleep Debt Backfill Script")
    logger.info("=" * 60)

    try:
        backfill_sleep_debt(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Error during backfill: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
