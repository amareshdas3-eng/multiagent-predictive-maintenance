"""
app.py - Interactive FastAPI Web Server for Multi-Agent Predictive Maintenance.

Provides REST API endpoints and serves the modern real-time dashboard:
- Live LangGraph agent state coordination visualizer
- 1-Click asset diagnosis & custom parameter simulation
- Real-time agent thought logs
- SQLite work order history & export
"""

import os
import sys
import json
import webbrowser
import threading
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from database import (
    init_db,
    get_db_session,
    fetch_latest_telemetry,
    save_work_order,
    TelemetryRecord,
    WorkOrder
)
from seed_data import seed_database
from graph import run_pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
METADATA_PATH = os.path.join(BASE_DIR, "data", "equipment_metadata.json")
CALENDAR_PATH = os.path.join(BASE_DIR, "data", "production_calendar.json")

# Ensure database is initialized
init_db()

app = FastAPI(title="Industrial Predictive Maintenance Agent Suite", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def load_metadata() -> Dict[str, Any]:
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class SimulationPayload(BaseModel):
    asset_id: str
    custom_parameters: Dict[str, float]


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/api/assets")
def get_assets():
    """Return all configured equipment with latest sensor stats."""
    metadata = load_metadata()
    assets_list = []
    for asset_id, meta in metadata.items():
        telemetry = fetch_latest_telemetry(asset_id, limit=8)
        assets_list.append({
            "asset_id": asset_id,
            "metadata": meta,
            "recent_telemetry": telemetry
        })
    return assets_list


@app.get("/api/telemetry/{asset_id}")
def get_telemetry(asset_id: str):
    """Retrieve recent time-series telemetry records for an asset."""
    records = fetch_latest_telemetry(asset_id, limit=30)
    return {"asset_id": asset_id, "records": records}


@app.post("/api/run/{asset_id}")
def run_asset_diagnosis(asset_id: str):
    """
    Executes the LangGraph predictive maintenance pipeline for the requested asset.
    Returns agent coordination steps, diagnostic result, and generated work order.
    """
    try:
        start_time = time.time()
        final_state = run_pipeline(asset_id)
        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "asset_id": asset_id,
            "execution_time_ms": execution_time_ms,
            "diagnostic_result": final_state.get("diagnostic_result", {}),
            "manual_guidelines": final_state.get("manual_guidelines", {}),
            "work_order": final_state.get("work_order", ""),
            "messages": final_state.get("messages", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulate")
def simulate_custom_telemetry(payload: SimulationPayload):
    """
    Injects custom parameter readings (e.g., winding_temp=115, dc_link_voltage=750)
    and executes the LangGraph multi-agent pipeline against the simulated values.
    """
    asset_id = payload.asset_id
    params = payload.custom_parameters

    custom_records = []
    for p_name, val in params.items():
        custom_records.append({
            "parameter_name": p_name,
            "value": val,
            "unit": "custom",
            "status": "SIMULATED"
        })

    try:
        start_time = time.time()
        final_state = run_pipeline(asset_id, custom_telemetry=custom_records)
        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "asset_id": asset_id,
            "execution_time_ms": execution_time_ms,
            "diagnostic_result": final_state.get("diagnostic_result", {}),
            "manual_guidelines": final_state.get("manual_guidelines", {}),
            "work_order": final_state.get("work_order", ""),
            "messages": final_state.get("messages", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/work_orders")
def get_work_orders():
    """Retrieve all work orders saved in the SQLite database."""
    session = get_db_session()
    try:
        orders = session.query(WorkOrder).order_by(WorkOrder.created_at.desc()).all()
        return [o.to_dict() for o in orders]
    finally:
        session.close()


@app.post("/api/reseed")
def reseed_data():
    """Reset and re-seed the SQLite database."""
    seed_database()
    return {"success": True, "message": "Database reseeded successfully with realistic sensor telemetry."}


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    # Check if database has records; if not, seed it
    session = get_db_session()
    try:
        count = session.query(TelemetryRecord).count()
        if count == 0:
            seed_database()
    finally:
        session.close()

    print("[*] Starting Industrial Predictive Maintenance Interactive Application...")
    print("[*] Local URL: http://127.0.0.1:8000")
    
    # Auto-open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
