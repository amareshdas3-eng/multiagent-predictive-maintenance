"""
agents/work_order_scheduler.py - Specialized LangGraph node for Work Order Generation & Scheduling.

Evaluates diagnostic severity, coordinates with simulated production calendar JSON,
generates formal electrical engineering Work Orders, and commits them to the local SQLite database.
"""

import os
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from database import save_work_order

SYSTEM_PROMPT = """You are an Industrial Maintenance Planner and Scheduling Agent.

Your goal is to take the diagnostic summary and troubleshooting steps, check a simulated local production calendar JSON, and schedule an optimized work order.

Instructions:
1. Assign a priority based on fault severity (Critical = Immediate Shutdown / 2-hour window, High = Within 24 hours, Medium = Next scheduled outage).
2. Generate a formal Work Order document including:
   - Work Order ID (auto-generated alphanumeric)
   - Asset ID & Location
   - Required LOTO (Lockout/Tagout) and safety permits
   - Required spares/tools (e.g., infrared camera, OMICRON test kit, torque wrench)
   - Estimated downtime duration
3. Write the generated work order record back to the local SQLite `WorkOrder` table.

Output format: Return the complete formatted Work Order markdown string for display in the CLI or Streamlit UI.
"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALENDAR_PATH = os.path.join(BASE_DIR, "data", "production_calendar.json")
METADATA_PATH = os.path.join(BASE_DIR, "data", "equipment_metadata.json")


def load_calendar_and_metadata():
    calendar = {}
    metadata = {}
    if os.path.exists(CALENDAR_PATH):
        with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
            calendar = json.load(f)
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    return calendar, metadata


def work_order_scheduler_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: Work Order & Maintenance Scheduler Agent.
    Generates formal Work Order document, schedules work slot, and saves to SQLite.
    """
    asset_id = state.get("asset_id", "UNKNOWN")
    diagnostic = state.get("diagnostic_result", {})
    manual_data = state.get("manual_guidelines", {})
    severity = diagnostic.get("severity", "Medium")

    calendar, metadata = load_calendar_and_metadata()
    asset_meta = metadata.get(asset_id, {})
    location = asset_meta.get("location", "Main Plant Floor")
    loto_points = asset_meta.get("loto_isolation_points", [
        "Open incoming feeder breaker and apply LOTO padlock",
        "Verify dead using calibrated tester before starting work"
    ])

    # 1. Assign Priority & Scheduling Slot based on Severity
    now = datetime.now(timezone.utc)
    if severity == "Critical":
        priority = "Critical"
        scheduled_slot = f"{now.strftime('%Y-%m-%d %H:%M UTC')} (Immediate Emergency Shutdown / 2-Hour Window)"
        downtime_duration = "4 Hours"
        permit_type = "Class 1 Emergency Live-Switching & Confined Isolation Permit"
    elif severity == "High":
        priority = "High"
        scheduled_slot = f"{(now + timedelta(hours=14)).strftime('%Y-%m-%d %H:%M UTC')} (Next Off-Peak Window, Shift 3)"
        downtime_duration = "6 Hours"
        permit_type = "Class 2 Planned Electrical Isolation & Hot-Work Permit"
    else:
        priority = "Medium"
        scheduled_slot = "2026-10-25 01:00 UTC (Next Scheduled Plant Maintenance Outage)"
        downtime_duration = "8 Hours"
        permit_type = "Class 3 Routine Preventative Maintenance Permit"

    # Auto-generate Work Order ID
    random_code = random.randint(1000, 9999)
    clean_asset = asset_id.replace("-", "").upper()
    order_id = f"WO-2026-{clean_asset}-{random_code}"

    # Required Tools and Spares based on Asset Category
    asset_upper = asset_id.upper()
    if "TR" in asset_upper:
        spares_and_tools = [
            "5kV Motorized Megger (Insulation Resistance & PI Tester)",
            "Calibrated High-Precision Torque Wrench (range 40-150 Nm)",
            "Part #FAN-TR-2500KVA Tangential Blower Fan Replacement Motor Assembly",
            "FLIR T1020 HD Infrared Thermal Camera",
            "3-Wire PT100 RTD Temperature Sensor Probes (Qty 2)",
            "Contact Cleaner Aerosol & Grade 8.8 High-Tensile M12/M16 Fasteners"
        ]
    elif "MCC" in asset_upper:
        spares_and_tools = [
            "OMICRON CPC 100 / Secondary Current Injection Test Set",
            "100A Micro-Ohmmeter (Ductor) for Busbar Joint Resistance",
            "Siemens/Schneider 3200A Contactor Main Contact Tip Replacement Kit",
            "110V AC Contactor Control Solenoid Coil & Shading Rings",
            "Belleville Conical Spring Washers (Cu busbar compatible)",
            "Calibrated Torque Wrench (calibrated for 45 Nm & 75 Nm)"
        ]
    elif "VFD" in asset_upper:
        spares_and_tools = [
            "Fluke CAT IV 1000V True-RMS Digital Multimeter with 1000V Probes",
            "Class 0 (1000V) Electrical Rubber Insulating Gloves with Leather Protectors",
            "Semikron/Infineon 1200V 600A Dual IGBT Replacement Module",
            "Thermal Interface Material (TIM) High-Conductivity Paste",
            "VFD Internal Heatsink Blower Fan & Tachometer Feedback Harness",
            "Dynamic Braking Resistor (DBR) 15-Ohm High-Power Ceramic Bank"
        ]
    else:
        spares_and_tools = [
            "Digital Multimeter CAT IV 1000V",
            "Insulation Resistance Tester 1000V",
            "Standard Insulated Hand Tool Kit"
        ]

    # Format LOTO string for database storage
    loto_db_text = "\n".join([f"- {step}" for step in loto_points])

    # 2. Persist to SQLite WorkOrder table
    db_order_payload = {
        "order_id": order_id,
        "asset_id": asset_id,
        "fault_detected": diagnostic.get("fault_detected", True),
        "priority": priority,
        "required_loto_steps": loto_db_text,
        "scheduled_date": scheduled_slot,
        "status": "APPROVED_PENDING_DISPATCH",
        "summary": f"{diagnostic.get('fault_category')} - {diagnostic.get('recommended_action')}"
    }
    save_work_order(db_order_payload)

    # 3. Generate Formal Work Order Markdown Document
    steps_md = "\n".join(manual_data.get("troubleshooting_steps", ["Perform standard visual check."]))
    spares_md = "\n".join([f"- {tool}" for tool in spares_and_tools])
    loto_md = "\n".join([f"- [ ] {point}" for point in loto_points])
    manuals_md = "\n".join([f"- {ref}" for ref in manual_data.get("referenced_manuals", ["Standard Operating Procedures"])])

    work_order_markdown = f"""# ==============================================================================
# INDUSTRIAL ELECTRICAL WORK ORDER: {order_id}
# ==============================================================================

**ASSET INFORMATION:**
- **Asset ID:** `{asset_id}`
- **Asset Description:** {asset_meta.get("asset_name", "Heavy Electrical Asset")}
- **Location:** {location}
- **Voltage / Rating:** {asset_meta.get("voltage_rating", "Industrial Power")} | {asset_meta.get("capacity_kva") or asset_meta.get("power_rating_kw") or asset_meta.get("rated_busbar_current_amps")}

**DIAGNOSTIC & SCHEDULING DETAILS:**
- **Fault Category:** {diagnostic.get("fault_category", "Electrical Fault")}
- **Severity Classification:** **[{priority.upper()}]**
- **Scheduled Maintenance Slot:** {scheduled_slot}
- **Estimated Downtime Duration:** {downtime_duration}
- **Safety Permit Required:** {permit_type}

---

### 1. DIAGNOSTIC ROOT CAUSE SUMMARY
> {diagnostic.get("diagnostic_summary", "No diagnostic summary available.")}

---

### 2. MANDATORY LOCKOUT / TAGOUT (LOTO) & SAFETY ISOLATION STEPS
{loto_md}

> **SAFETY ALERT:**
> {manual_data.get("safety_warnings", "Observe all NFPA 70E and local electrical safety guidelines.")}

---

### 3. REQUIRED TEST INSTRUMENTS & OEM SPARE PARTS
{spares_md}

---

### 4. SEQUENTIAL OEM TROUBLESHOOTING CHECKLIST
{steps_md}

---

### 5. REFERENCED STANDARDS & OEM MANUAL SECTIONS
{manuals_md}

---
*Work Order logged to SQLite database (`plant_maintenance.db`). Status: **APPROVED_PENDING_DISPATCH***
# ==============================================================================
"""

    thought = (
        f"[Work Order & Maintenance Scheduler Agent]\n"
        f"Generated Work Order: {order_id}\n"
        f"Priority: {priority} | Scheduled Window: {scheduled_slot}\n"
        f"Estimated Downtime: {downtime_duration} | Permit: {permit_type}\n"
        f"Persisted to SQLite database table 'work_orders'."
    )

    messages = state.get("messages", [])
    messages.append({"role": "work_order_scheduler_agent", "content": thought})

    return {
        **state,
        "work_order": work_order_markdown,
        "messages": messages
    }
