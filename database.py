"""
database.py - Root re-export for src.database module.
Provides backward compatibility for imports from the project root.
"""

from src.database import (
    DB_PATH,
    DATABASE_URL,
    engine,
    SessionLocal,
    Base,
    TelemetryRecord,
    MaintenanceManual,
    WorkOrder,
    init_db,
    get_db_session,
    fetch_latest_telemetry,
    search_manuals,
    save_work_order,
    utc_now
)

__all__ = [
    "DB_PATH",
    "DATABASE_URL",
    "engine",
    "SessionLocal",
    "Base",
    "TelemetryRecord",
    "MaintenanceManual",
    "WorkOrder",
    "init_db",
    "get_db_session",
    "fetch_latest_telemetry",
    "search_manuals",
    "save_work_order",
    "utc_now",
]
