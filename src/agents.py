"""
src/agents.py - Telemetry, RCA, and Scheduler Agent Definitions for Heavy Electrical Assets.

Implements:
1. TelemetryDiagnosticsAgent: Diagnoses thermal spikes, THD harmonics, and load unbalance.
2. ManualRCAgent: Queries local standards (IEC 60076, IEEE C37.20) and OEM troubleshooting checklists.
3. WorkOrderSchedulerAgent: Determines LOTO permits, reserves spare parts, and commits work orders to SQLite.
"""

import os
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from src.database import search_manuals, save_work_order

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALENDAR_PATH = os.path.join(BASE_DIR, "data", "production_calendar.json")
METADATA_PATH = os.path.join(BASE_DIR, "data", "equipment_metadata.json")
MANUALS_PATH = os.path.join(BASE_DIR, "data", "equipment_manuals.json")


# ==============================================================================
# AGENT 1: TELEMETRY DIAGNOSTICS AGENT
# ==============================================================================
TELEMETRY_SYSTEM_PROMPT = """You are an expert Senior Electrical Reliability and Diagnostic Agent specializing in heavy industrial power systems (11kV Transformers, Motor Control Centers, and VFDs). 

Your task is to analyze incoming real-time or historical telemetry windows and diagnose root anomalies based on electrical engineering principles:
- For 11kV Transformers: Look for winding temperature spikes (>95°C alarm, >110°C trip), cooling fan failure indicators, and abnormal load/current asymmetry.
- For MCCs: Look for busbar thermal overload, frequent thermal relay trips, and contactor chatter signatures.
- For VFDs: Look for DC-link overvoltage, IGBT overtemperature, output phase imbalance, and high total harmonic distortion (THD).

Input: A JSON object containing recent telemetry logs for a target asset.
Output: Return a structured JSON response containing:
- "asset_id": string
- "fault_detected": boolean
- "fault_category": string
- "severity": "Low" | "Medium" | "High" | "Critical"
- "diagnostic_summary": technical explanation of electrical root cause
- "recommended_action": string
"""


def analyze_telemetry_heuristics(asset_id: str, telemetry_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Expert electrical diagnostic engine evaluating physical thresholds and failure signatures."""
    params: Dict[str, List[float]] = {}
    for r in telemetry_records:
        p_name = r.get("parameter_name")
        val = r.get("value")
        if p_name and val is not None:
            params.setdefault(p_name, []).append(float(val))

    latest = {k: v[0] for k, v in params.items() if v}
    max_vals = {k: max(v) for k, v in params.items() if v}
    asset_upper = asset_id.upper()

    # 1. 11kV Transformers
    if "TR" in asset_upper or "TRANSFORMER" in asset_upper:
        winding_temp = max_vals.get("winding_temp", latest.get("winding_temp", 60.0))
        fan_status = latest.get("cooling_fan_status", 1.0)
        fan_rpm = latest.get("cooling_fan_rpm", 1450.0)
        curr_a = latest.get("load_current_phase_a", 100.0)
        curr_b = latest.get("load_current_phase_b", 100.0)
        curr_c = latest.get("load_current_phase_c", 100.0)

        avg_curr = (curr_a + curr_b + curr_c) / 3.0 if (curr_a + curr_b + curr_c) > 0 else 1.0
        max_dev = max(abs(curr_a - avg_curr), abs(curr_b - avg_curr), abs(curr_c - avg_curr))
        unbalance_pct = (max_dev / avg_curr) * 100.0

        if winding_temp >= 110.0:
            return {
                "asset_id": asset_id,
                "fault_detected": True,
                "fault_category": "Thermal Overload & Cooling Failure",
                "severity": "Critical",
                "diagnostic_summary": (
                    f"CRITICAL winding temperature excursion detected at {winding_temp:.1f}°C, exceeding the "
                    f"IEC 60076-11 Class F emergency trip threshold (110.0°C). Active cooling fan status is FAULT "
                    f"({fan_rpm:.0f} RPM), indicating complete forced-air cooling blower loss. Concurrently, severe "
                    f"phase load current unbalance ({unbalance_pct:.1f}% deviation, Phase A: {curr_a}A vs Phase B: {curr_b}A) "
                    f"is generating asymmetric magnetic flux saturation and localized hot spots in the HV winding core."
                ),
                "recommended_action": (
                    "Initiate immediate emergency load shedding or bus transfer. Lock out 11kV VCB and perform "
                    "post-overheat 5kV Megger insulation resistance testing, inspect cooling fan contactor circuit, "
                    "and verify busbar joint torque specs."
                )
            }
        elif winding_temp >= 95.0 or fan_status == 0.0 or unbalance_pct > 15.0:
            return {
                "asset_id": asset_id,
                "fault_detected": True,
                "fault_category": "Cooling System Degradation",
                "severity": "High",
                "diagnostic_summary": (
                    f"Winding temperature elevated at {winding_temp:.1f}°C (alarm threshold 95°C). "
                    f"Cooling blower status indicates degraded or intermittent airflow ({fan_rpm:.0f} RPM). "
                    f"Phase current asymmetry observed at {unbalance_pct:.1f}%."
                ),
                "recommended_action": (
                    "Inspect blower auxiliary supply, clean air intake filters, and re-balance secondary distribution feeders."
                )
            }
        else:
            return {
                "asset_id": asset_id,
                "fault_detected": False,
                "fault_category": "None",
                "severity": "Low",
                "diagnostic_summary": (
                    f"11kV Transformer operating normally. Winding temperature is stable at {winding_temp:.1f}°C "
                    f"(well below 95°C alarm threshold). Forced-air cooling fans are operational at {fan_rpm:.0f} RPM, "
                    f"and phase currents are balanced within {unbalance_pct:.1f}%."
                ),
                "recommended_action": "Continue routine thermographic and telemetry logging per standard PM schedule."
            }

    # 2. Motor Control Centers (MCC)
    elif "MCC" in asset_upper:
        busbar_temp = max_vals.get("busbar_temperature", latest.get("busbar_temperature", 45.0))
        chatter_events = max_vals.get("contactor_chatter_events_hr", latest.get("contactor_chatter_events_hr", 0.0))
        coil_voltage = latest.get("control_coil_voltage", 110.0)
        relay_trips = max_vals.get("thermal_relay_trip_count", latest.get("thermal_relay_trip_count", 0.0))

        if busbar_temp >= 85.0 or chatter_events >= 10.0 or relay_trips >= 3.0:
            severity = "Critical" if (busbar_temp >= 88.0 or chatter_events >= 15.0) else "High"
            return {
                "asset_id": asset_id,
                "fault_detected": True,
                "fault_category": "Busbar Thermal Overload & Contactor Instability",
                "severity": severity,
                "diagnostic_summary": (
                    f"MCC busbar joint temperature spiked to {busbar_temp:.1f}°C, violating IEEE C37.20.1 "
                    f"thermal limits (nominal alarm 75°C, max limit 90°C). Severe contactor chatter detected at "
                    f"{chatter_events:.0f} events/hr, triggered by control bus under-voltage ({coil_voltage:.1f}V AC). "
                    f"Contactor bouncing has induced arc pitting and thermal relay trips ({relay_trips:.0f} trips/shift), "
                    f"posing immediate risk of contact welding and phase-to-phase flashover."
                ),
                "recommended_action": (
                    "Schedule immediate breaker isolation and LOTO. Perform micro-ohmmeter (Ductor) test on busbar splices, "
                    "retorque bolted connections to 75 Nm, and replace degraded 110V control transformer coil contactor assembly."
                )
            }
        elif busbar_temp >= 75.0 or chatter_events >= 3.0:
            return {
                "asset_id": asset_id,
                "fault_detected": True,
                "fault_category": "Thermal & Control Degradation",
                "severity": "Medium",
                "diagnostic_summary": (
                    f"Elevated busbar temperature at {busbar_temp:.1f}°C and minor contactor chatter ({chatter_events:.0f} events/hr). "
                    f"Indicates early joint oxidation or control supply fluctuations."
                ),
                "recommended_action": "Perform thermography scan and check control circuit power supply regulation."
            }
        else:
            return {
                "asset_id": asset_id,
                "fault_detected": False,
                "fault_category": "None",
                "severity": "Low",
                "diagnostic_summary": (
                    f"MCC busbar and feeder breakers operating within standard parameters. Busbar temperature at {busbar_temp:.1f}°C "
                    f"(limit 75°C), zero contactor chatter detected, and control coil voltage nominal at {coil_voltage:.1f}V AC."
                ),
                "recommended_action": "Maintain quarterly infrared inspection and routine cleaning."
            }

    # 3. Variable Frequency Drives (VFD)
    elif "VFD" in asset_upper:
        dc_link = max_vals.get("dc_link_voltage", latest.get("dc_link_voltage", 580.0))
        igbt_temp = max_vals.get("igbt_temperature", latest.get("igbt_temperature", 55.0))
        thd = max_vals.get("harmonic_distortion", latest.get("harmonic_distortion", 3.0))
        phase_imbalance = latest.get("output_phase_imbalance", 2.0)
        fan_rpm = latest.get("heatsink_fan_rpm", 1800.0)

        if dc_link >= 740.0 or igbt_temp >= 95.0 or thd >= 10.0:
            return {
                "asset_id": asset_id,
                "fault_detected": True,
                "fault_category": "DC-Link Overvoltage & Power Semiconductor Thermal Stress",
                "severity": "Critical",
                "diagnostic_summary": (
                    f"Critical VFD electrical anomaly: DC-link voltage surged to {dc_link:.1f}V DC, breaching the "
                    f"740V emergency trip threshold. IGBT junction temperature escalated to {igbt_temp:.1f}°C (limit 95°C), "
                    f"accelerated by restricted heatsink cooling ({fan_rpm:.0f} RPM) and excessive current Total Harmonic "
                    f"Distortion (THD) at {thd:.1f}% (IEEE 519 limit 5.0%). Output phase imbalance is {phase_imbalance:.1f}%, "
                    f"indicating potential gate driver desaturation or regenerative overhauling without proper dynamic braking."
                ),
                "recommended_action": (
                    "Controlled trip of drive. CRITICAL SAFETY: Implement LOTO and wait minimum 10 minutes for DC bus "
                    "capacitors to discharge below 50V DC before opening enclosure. Inspect dynamic braking resistor (DBR), "
                    "clean heatsink fins, and inspect IGBT gate driver boards."
                )
            }
        elif dc_link >= 700.0 or igbt_temp >= 85.0 or thd >= 5.0:
            return {
                "asset_id": asset_id,
                "fault_detected": True,
                "fault_category": "Harmonic Distortion & Thermal Pre-Alarm",
                "severity": "High",
                "diagnostic_summary": (
                    f"VFD telemetry indicates elevated harmonics ({thd:.1f}% THD) and rising IGBT temperature ({igbt_temp:.1f}°C). "
                    f"DC link voltage is elevated at {dc_link:.1f}V DC."
                ),
                "recommended_action": "Inspect line input reactor, test heatsink blower fan, and log motor shaft voltages."
            }
        else:
            return {
                "asset_id": asset_id,
                "fault_detected": False,
                "fault_category": "None",
                "severity": "Low",
                "diagnostic_summary": (
                    f"VFD drive power stage healthy. DC-link voltage stable at {dc_link:.1f}V DC (nominal 565-650V), "
                    f"IGBT temperature is safe at {igbt_temp:.1f}°C, and THD is compliant at {thd:.1f}%."
                ),
                "recommended_action": "Continue regular filter and cooling channel preventive maintenance."
            }

    return {
        "asset_id": asset_id,
        "fault_detected": False,
        "fault_category": "None",
        "severity": "Low",
        "diagnostic_summary": f"Asset {asset_id} telemetry readings are within baseline operational tolerances.",
        "recommended_action": "Standard scheduled inspection."
    }


def telemetry_diagnostics_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Node: Telemetry Diagnostics Agent."""
    asset_id = state.get("asset_id", "UNKNOWN")
    telemetry_data = state.get("telemetry_data", {})
    records = telemetry_data.get("records", [])

    diagnostic_result = analyze_telemetry_heuristics(asset_id, records)

    thought = (
        f"[Telemetry Diagnostics Agent]\n"
        f"Target Asset: {asset_id}\n"
        f"Fault Detected: {diagnostic_result['fault_detected']}\n"
        f"Category: {diagnostic_result['fault_category']} | Severity: {diagnostic_result['severity']}\n"
        f"Diagnosis: {diagnostic_result['diagnostic_summary']}"
    )

    messages = state.get("messages", [])
    messages.append({"role": "telemetry_diagnostics_agent", "content": thought})

    return {
        **state,
        "diagnostic_result": diagnostic_result,
        "messages": messages
    }


# ==============================================================================
# AGENT 2: MANUAL RETRIEVAL & ROOT CAUSE ANALYSIS (RCA) AGENT
# ==============================================================================
RCA_SYSTEM_PROMPT = """You are an Electrical Maintenance Manual Specialist and Root Cause Analysis (RCA) Agent. 

When provided with a diagnostic fault summary from the Telemetry Agent, your job is to query the local vector store (or local text chunk index) containing manufacturer manuals and electrical standards (such as IEC 60076 for transformers and IEEE guidelines for switchgear).

Instructions:
1. Retrieve the top 3 most relevant maintenance manual sections or troubleshooting guidelines for the specific asset type and fault category.
2. Extract specific OEM recommended actions, torque specs, testing procedures (e.g., insulation resistance, secondary injection), or replacement criteria.
3. Formulate a step-by-step troubleshooting checklist for the maintenance crew.

Output format:
- "referenced_manuals": list of document titles and section numbers
- "troubleshooting_steps": numbered list of safe, sequential actions
- "safety_warnings": mandatory safety cautions
"""


def get_asset_type_from_id(asset_id: str) -> str:
    asset_upper = asset_id.upper()
    if "TR" in asset_upper or "TRANSFORMER" in asset_upper:
        return "Transformer"
    elif "MCC" in asset_upper:
        return "MCC"
    elif "VFD" in asset_upper:
        return "VFD"
    return "Electrical Asset"


def manual_retrieval_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Node: Manual Retrieval & RCA Agent."""
    asset_id = state.get("asset_id", "UNKNOWN")
    diagnostic = state.get("diagnostic_result", {})
    fault_category = diagnostic.get("fault_category", "")
    summary = diagnostic.get("diagnostic_summary", "")

    asset_type = get_asset_type_from_id(asset_id)

    search_query = f"{fault_category} {summary}"
    manual_chunks = search_manuals(asset_type=asset_type, query=search_query, limit=3)

    referenced_manuals = [
        f"{m['title']} - {m['section']}" for m in manual_chunks
    ]

    if asset_type == "Transformer":
        troubleshooting_steps = [
            "1. De-energize 11kV primary feeder: Open and rack out Vacuum Circuit Breaker (VCB) and open LV incomer ACB.",
            "2. Apply safety grounds to 11kV terminals using certified HV grounding cluster; apply Lockout/Tagout (LOTO) padlocks.",
            "3. Conduct 5kV motorized Megger Insulation Resistance (IR) test between HV-Earth, LV-Earth, and HV-LV windings. Verify R_1min >= 1000 Mega-ohms and Polarization Index (PI) >= 2.0 per IEC 60076-11.",
            "4. Inspect forced-air tangential cooling fan blowers: Test coil winding resistance, spin impellers manually to detect bearing seizure, and check 24VDC/230VAC fan control relays.",
            "5. Verify bolted joint torque using a calibrated torque wrench: HV terminals (M12) to 85 Nm; LV copper links (M16) to 120 Nm.",
            "6. Inspect secondary distribution phases with clamp meter to locate and rebalance unbalance source causing asymmetric load flux."
        ]
        safety_warnings = (
            "DANGER: 11,000 VOLTS HV HAZARD. Prior to any contact, verify dead using an acoustic/optical HV detector "
            "and attach physical grounding links to both primary and secondary busbars. Maintain minimum safety distance "
            "per IEC 61936-1."
        )
    elif asset_type == "MCC":
        troubleshooting_steps = [
            "1. Execute Arc-Flash Hazard Isolation: Rack out MCC-02 Main Incomer ACB-3200A and confirm test/disconnected position.",
            "2. Apply multi-lock LOTO hasp to ACB crank shutter and isolate 110V AC control power supply switch FS-CTRL-02.",
            "3. Inspect main busbar splice plates with FLIR thermal imaging reference; check Belleville spring washers for annealing.",
            "4. Perform micro-ohmmeter (Ductor) 100A test across all busbar joints; verify resistance is < 15 micro-ohms.",
            "5. Retorque all busbar fasteners to OEM specification: M10 grade 8.8 bolts = 45 Nm; M12 bolts = 75 Nm. Apply torque seal inspection lacquer.",
            "6. Measure 110V AC control transformer voltage under simulated contactor pickup load to eliminate under-voltage chatter.",
            "7. Inspect contactor main tips for erosion/pitting (replace if wear > 1.5mm) and inspect magnetic core shading rings for cracks.",
            "8. Perform secondary current injection test on thermal-magnetic trip units using secondary test kit to calibrate pickup curve."
        ]
        safety_warnings = (
            "WARNING: ARC-FLASH HAZARD CATEGORY 4 (Incident Energy > 40 cal/cm^2). Personnel must wear full 40 cal/cm^2 "
            "Arc Flash Suit, balaclava, and Class 0 insulated gloves before operating rack-in/out mechanisms or testing busbars."
        )
    elif asset_type == "VFD":
        troubleshooting_steps = [
            "1. Open upstream feeder breaker (MCC-02-F08) and apply LOTO hasp to drive disconnect switch.",
            "2. CRITICAL DC-BUS DISCHARGE: Wait a minimum of 10 MINUTES for internal bleeder resistors to discharge DC capacitors.",
            "3. Don Class 0 (1000V) electrical insulating gloves and verify zero voltage across DC+ and DC- terminals with CAT IV 1000V multimeter (must be < 50V DC).",
            "4. Inspect Dynamic Braking Resistor (DBR) bank continuity, measuring ohmic resistance against nameplate value.",
            "5. Inspect heatsink cooling channel and tachometer feedback from internal blower fan; clear dust accretion using ESD-safe vacuum (< 2 bar dry air).",
            "6. Test IGBT power module diode bridge with digital multimeter in diode-test mode (nominal forward voltage drop 0.35V - 0.45V per module).",
            "7. Inspect optical fiber gate driver cables for optical attenuation or loose SMA connectors.",
            "8. Verify input line reactor impedance (3% - 5%) to mitigate harmonic injection per IEEE 519."
        ]
        safety_warnings = (
            "CRITICAL LIFE-SAFETY HAZARD: HIGH-CAPACITANCE STORED DC VOLTAGE (>740V DC). Turning off the input AC breaker "
            "does NOT discharge the DC link capacitor bank. Contact with energized DC bus is FATAL. Always wait 10 minutes "
            "and physically measure DC+ to DC- < 50V before touching any internal power terminal."
        )
    else:
        troubleshooting_steps = ["1. Isolate main breaker and execute LOTO.", "2. Perform insulation resistance and torque checks."]
        safety_warnings = "Ensure complete LOTO before opening equipment."

    manual_guidelines = {
        "asset_type": asset_type,
        "referenced_manuals": referenced_manuals,
        "troubleshooting_steps": troubleshooting_steps,
        "safety_warnings": safety_warnings
    }

    thought = (
        f"[Manual Retrieval & RCA Agent]\n"
        f"Asset Type: {asset_type} | Retrieved {len(referenced_manuals)} relevant standard/manual sections.\n"
        f"Referenced Manuals:\n" + "\n".join(f" - {m}" for m in referenced_manuals) + "\n"
        f"Safety Protocol: {safety_warnings[:150]}..."
    )

    messages = state.get("messages", [])
    messages.append({"role": "manual_retrieval_agent", "content": thought})

    return {
        **state,
        "manual_guidelines": manual_guidelines,
        "messages": messages
    }


# ==============================================================================
# AGENT 3: WORK ORDER & MAINTENANCE SCHEDULER AGENT
# ==============================================================================
SCHEDULER_SYSTEM_PROMPT = """You are an Industrial Maintenance Planner and Scheduling Agent.

Your goal is to take the diagnostic summary and troubleshooting steps, check a simulated local production calendar JSON, and schedule an optimized work order.

Instructions:
1. Assign a priority based on fault severity (Critical = Immediate Shutdown / 2-hour window, High = Within 24 hours, Medium = Next scheduled outage).
2. Generate a formal Work Order document including:
   - Work Order ID (auto-generated alphanumeric)
   - Asset ID & Location
   - Required LOTO (Lockout/Tagout) and safety permits
   - Required spares/tools
   - Estimated downtime duration
3. Write the generated work order record back to the local SQLite WorkOrder table.

Output format: Return the complete formatted Work Order markdown string.
"""


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
    """LangGraph Node: Work Order & Maintenance Scheduler Agent."""
    asset_id = state.get("asset_id", "UNKNOWN")
    diagnostic = state.get("diagnostic_result", {})
    manual_data = state.get("manual_guidelines", {})
    severity = diagnostic.get("severity", "Medium")

    calendar, metadata = load_calendar_and_metadata()
    asset_meta = metadata.get(asset_id, {})
    location = asset_meta.get("location", "Main Industrial Complex")
    loto_points = asset_meta.get("loto_isolation_points", [
        "Open incoming feeder breaker and apply LOTO padlock",
        "Verify dead using calibrated tester before starting work"
    ])

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

    random_code = random.randint(1000, 9999)
    clean_asset = asset_id.replace("-", "").upper()
    order_id = f"WO-2026-{clean_asset}-{random_code}"

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

    loto_db_text = "\n".join([f"- {step}" for step in loto_points])

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
