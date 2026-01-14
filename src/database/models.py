"""
SQLAlchemy models for storing wellness and productivity data.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class WellnessRecord(Base):
    """Stores daily wellness metrics from Intervals.icu."""

    __tablename__ = 'wellness_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD

    # Sleep data
    sleep_seconds = Column(Integer)
    sleep_hours = Column(Float)
    sleep_quality = Column(Integer)  # 1-5 rating
    sleep_start = Column(String(25))  # ISO timestamp
    sleep_end = Column(String(25))    # ISO timestamp

    # Recovery metrics
    resting_hr = Column(Float)
    hrv_rmssd = Column(Float)

    # Baseline comparison
    baseline_hrv = Column(Float)
    baseline_rhr = Column(Float)
    baseline_sleep = Column(Float)

    # Subjective metrics
    mood = Column(Integer)
    fatigue = Column(Integer)
    stress = Column(Integer)
    soreness = Column(Integer)
    weight = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    productivity_scores = relationship("ProductivityScore", back_populates="wellness_record", cascade="all, delete-orphan")
    daily_report = relationship("DailyReport", back_populates="wellness_record", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WellnessRecord(date='{self.date}', sleep={self.sleep_hours}h, hrv={self.hrv_rmssd})>"


class ProductivityScore(Base):
    """Stores hourly productivity scores for each day."""

    __tablename__ = 'productivity_scores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wellness_record_id = Column(Integer, ForeignKey('wellness_records.id'), nullable=False)

    hour = Column(Integer, nullable=False)  # 0-23
    score = Column(Float, nullable=False)   # 0-100

    # Component scores
    circadian_component = Column(Float)
    recovery_component = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wellness_record = relationship("WellnessRecord", back_populates="productivity_scores")

    def __repr__(self):
        return f"<ProductivityScore(hour={self.hour}, score={self.score:.1f})>"


class DailyReport(Base):
    """Stores generated AI reports and summaries."""

    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wellness_record_id = Column(Integer, ForeignKey('wellness_records.id'), unique=True, nullable=False)

    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    # AI-generated content
    ai_insight = Column(Text)
    full_report = Column(Text)
    quick_summary = Column(Text)

    # Summary statistics
    recovery_score = Column(Float)
    recovery_status = Column(String(20))
    average_productivity = Column(Float)
    peak_hours = Column(JSON)  # Store as JSON array
    time_blocks = Column(JSON)  # Recommended focus blocks

    # Delivery status
    google_doc_id = Column(String(100))
    delivered_at = Column(DateTime)
    delivery_status = Column(String(20), default='pending')  # pending, delivered, failed

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wellness_record = relationship("WellnessRecord", back_populates="daily_report")

    def __repr__(self):
        return f"<DailyReport(date='{self.date}', status='{self.delivery_status}')>"
