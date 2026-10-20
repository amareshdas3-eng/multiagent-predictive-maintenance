"""
agents/manual_retrieval.py - Specialized LangGraph node for Manual Retrieval & Root Cause Analysis (RCA).

Queries local documentation / text chunk index containing manufacturer manuals and
electrical standards (IEC 60076 for transformers, IEEE C37.20.1/141 for switchgear, VFD OEM guides).
Extracts OEM recommended actions, torque specs, testing procedures, and generates safe checklists.
"""

import os
import json
from typing import Dict, Any, List
from database import search_manuals

SYSTEM_PROMPT = """You are an Electrical Maintenance Manual Specialist and Root Cause Analysis (RCA) Agent. 

When provided with a diagnostic fault summary from the Telemetry Agent, your job is to query the local vector store (or local text chunk index) containing manufacturer manuals and electrical standards (such as IEC 60076 for transformers and IEEE guidelines for switchgear).

Instructions:
1. Retrieve the top 3 most relevant maintenance manual sections or troubleshooting guidelines for the specific asset type and fault category.
2. Extract specific OEM recommended actions, torque specs, testing procedures (e.g., insulation resistance, secondary injection), or replacement criteria.
3. Formulate a step-by-step troubleshooting checklist for the maintenance crew.

Output format:
- "referenced_manuals": list of document titles and section numbers
- "troubleshooting_steps": numbered list of safe, sequential actions
- "safety_warnings": mandatory safety cautions (e.g., "Ensure complete LOTO and discharge capacitive stored energy before opening VFD enclosure").
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
    """
    LangGraph Node: Manual Retrieval & RCA Agent.
    Queries SQLite MaintenanceManual chunks and produces OEM troubleshooting procedures.
    """
    asset_id = state.get("asset_id", "UNKNOWN")
    diagnostic = state.get("diagnostic_result", {})
    fault_category = diagnostic.get("fault_category", "")
    summary = diagnostic.get("diagnostic_summary", "")

    asset_type = get_asset_type_from_id(asset_id)

    # Search local SQLite maintenance manuals
    search_query = f"{fault_category} {summary}"
    manual_chunks = search_manuals(asset_type=asset_type, query=search_query, limit=3)

    referenced_manuals = [
        f"{m['title']} - {m['section']}" for m in manual_chunks
    ]

    # Formulate asset-specific troubleshooting checklists, torque specs, and safety warnings
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
        troubleshooting_steps = [
            "1. Isolate main power supply breaker and confirm zero voltage.",
            "2. Perform insulation resistance and continuity testing.",
            "3. Inspect mechanical terminals and retorque to manufacturer specifications."
        ]
        safety_warnings = "Ensure complete Lockout/Tagout (LOTO) before commencing work."

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
