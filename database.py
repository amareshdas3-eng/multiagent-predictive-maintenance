"""
database.py - Local SQLite Database Layer for Electrical Predictive Maintenance.

Replaces MongoDB Atlas with a local SQLite database using SQLAlchemy.
Provides models for TelemetryRecord, MaintenanceManual, and WorkOrder.
"""

import os
from datetime import datetime, timezone
from typing import Generator, List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    desc
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Define SQLite database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "plant_maintenance.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy Engine & Session
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class TelemetryRecord(Base):
    """
    Stores time-series sensor readings for heavy industrial electrical assets.
    Example assets: 11kV Transformers, MCCs, VFDs.
    """
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    asset_id = Column(String(50), nullable=False, index=True)
    parameter_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    status = Column(String(20), default="NORMAL", nullable=False)  # NORMAL, WARNING, CRITICAL

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "asset_id": self.asset_id,
            "parameter_name": self.parameter_name,
            "value": self.value,
            "unit": self.unit,
            "status": self.status
        }


class MaintenanceManual(Base):
    """
    Stores chunked maintenance manuals, OEM guidelines, and electrical standards
    (IEC 60076, IEEE C37.20.1, VFD OEM manuals).
    """
    __tablename__ = "maintenance_manuals"

    doc_id = Column(String(50), primary_key=True)
    asset_type = Column(String(50), nullable=False, index=True)  # Transformer, MCC, VFD
    title = Column(String(200), nullable=False)
    section = Column(String(100), nullable=False)
    content_chunk = Column(Text, nullable=False)

    def to_dict(self):
        return {
            "doc_id": self.doc_id,
            "asset_type": self.asset_type,
            "title": self.title,
            "section": self.section,
            "content_chunk": self.content_chunk
        }


class WorkOrder(Base):
    """
    Stores generated maintenance work orders with safety LOTO requirements
    and scheduling details.
    """
    __tablename__ = "work_orders"

    order_id = Column(String(50), primary_key=True)
    asset_id = Column(String(50), nullable=False, index=True)
    fault_detected = Column(Boolean, default=True, nullable=False)
    priority = Column(String(20), nullable=False)  # Critical, High, Medium, Low
    required_loto_steps = Column(Text, nullable=False)
    scheduled_date = Column(String(50), nullable=False)
    status = Column(String(30), default="PENDING_DISPATCH", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    summary = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "asset_id": self.asset_id,
            "fault_detected": self.fault_detected,
            "priority": self.priority,
            "required_loto_steps": self.required_loto_steps,
            "scheduled_date": self.scheduled_date,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "summary": self.summary
        }


def init_db():
    """Create all tables in SQLite database."""
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Provide a new SQLAlchemy session."""
    return SessionLocal()


def fetch_latest_telemetry(asset_id: str, limit: int = 50) -> List[dict]:
    """Retrieve the most recent telemetry readings for an asset."""
    session = SessionLocal()
    try:
        records = (
            session.query(TelemetryRecord)
            .filter(TelemetryRecord.asset_id == asset_id)
            .order_by(desc(TelemetryRecord.timestamp))
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in records]
    finally:
        session.close()


def search_manuals(asset_type: str, query: str = "", limit: int = 3) -> List[dict]:
    """
    Search maintenance manual chunks for an asset type matching query terms.
    Uses keyword/token relevance ranking over SQLite chunks.
    """
    session = SessionLocal()
    try:
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        manuals = (
            session.query(MaintenanceManual)
            .filter(MaintenanceManual.asset_type.ilike(f"%{asset_type}%"))
            .all()
        )
        
        if not query_terms:
            return [m.to_dict() for m in manuals[:limit]]

        scored = []
        for m in manuals:
            content_lower = (m.title + " " + m.section + " " + m.content_chunk).lower()
            score = sum(content_lower.count(term) * (3 if term in m.section.lower() else 1) for term in query_terms)
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m.to_dict() for score, m in scored[:limit]]
    finally:
        session.close()


def save_work_order(order_data: dict) -> WorkOrder:
    """Persist a newly scheduled work order into SQLite."""
    session = SessionLocal()
    try:
        work_order = WorkOrder(
            order_id=order_data["order_id"],
            asset_id=order_data["asset_id"],
            fault_detected=order_data.get("fault_detected", True),
            priority=order_data["priority"],
            required_loto_steps=order_data["required_loto_steps"],
            scheduled_date=str(order_data["scheduled_date"]),
            status=order_data.get("status", "SCHEDULED"),
            summary=order_data.get("summary", "")
        )
        merged = session.merge(work_order)
        session.commit()
        session.refresh(merged)
        return merged
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
