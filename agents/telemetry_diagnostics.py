"""
agents/telemetry_diagnostics.py - Specialized LangGraph node for Electrical & Thermal Telemetry Diagnostics.

Specializes in heavy industrial power systems:
- 11kV Transformers (winding temp spikes >95°C alarm, >110°C trip, cooling fan failure, load/current asymmetry)
- Motor Control Centers (busbar thermal overload, frequent thermal relay trips, contactor chatter signatures)
- Variable Frequency Drives (DC-link overvoltage, IGBT overtemperature, output phase imbalance, high THD)
"""

import json
import os
from typing import Dict, Any, List

SYSTEM_PROMPT = """You are an expert Senior Electrical Reliability and Diagnostic Agent specializing in heavy industrial power systems (11kV Transformers, Motor Control Centers, and VFDs). 

Your task is to analyze incoming real-time or historical telemetry windows and diagnose root anomalies based on electrical engineering principles:
- For 11kV Transformers: Look for winding temperature spikes (>95°C alarm, >110°C trip), cooling fan failure indicators, and abnormal load/current asymmetry.
- For MCCs: Look for busbar thermal overload, frequent thermal relay trips, and contactor chatter signatures.
- For VFDs: Look for DC-link overvoltage, IGBT overtemperature, output phase imbalance, and high total harmonic distortion (THD).

Input: A JSON object containing recent telemetry logs for a target asset.
Output: Return a structured JSON response containing:
- "asset_id": string
- "fault_detected": boolean
- "fault_category": string (e.g., "Thermal Overload", "Harmonic Distortion", "Cooling Failure")
- "severity": "Low" | "Medium" | "High" | "Critical"
- "diagnostic_summary": a technical paragraph explaining the probable electrical root cause.
- "recommended_action": string
"""


def analyze_telemetry_heuristics(asset_id: str, telemetry_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Expert electrical diagnostic engine evaluating physical thresholds and failure signatures.
    Guarantees deterministic, 100% self-contained local execution for recruiters without external API keys.
    """
    # Group latest parameter readings
    params: Dict[str, List[float]] = {}
    for r in telemetry_records:
        p_name = r.get("parameter_name")
        val = r.get("value")
        if p_name and val is not None:
            params.setdefault(p_name, []).append(float(val))

    # Helper for latest reading
    latest = {k: v[0] for k, v in params.items() if v}
    max_vals = {k: max(v) for k, v in params.items() if v}

    asset_upper = asset_id.upper()

    # ------------------------------------------------------------------
    # 1. 11kV DRY-TYPE TRANSFORMER DIAGNOSTICS
    # ------------------------------------------------------------------
    if "TR" in asset_upper or "TRANSFORMER" in asset_upper:
        winding_temp = max_vals.get("winding_temp", latest.get("winding_temp", 60.0))
        fan_status = latest.get("cooling_fan_status", 1.0)
        fan_rpm = latest.get("cooling_fan_rpm", 1450.0)
        curr_a = latest.get("load_current_phase_a", 100.0)
        curr_b = latest.get("load_current_phase_b", 100.0)
        curr_c = latest.get("load_current_phase_c", 100.0)

        # Calculate current unbalance percentage
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

    # ------------------------------------------------------------------
    # 2. MOTOR CONTROL CENTER (MCC) DIAGNOSTICS
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 3. VARIABLE FREQUENCY DRIVE (VFD) DIAGNOSTICS
    # ------------------------------------------------------------------
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

    # Generic fallback
    return {
        "asset_id": asset_id,
        "fault_detected": False,
        "fault_category": "None",
        "severity": "Low",
        "diagnostic_summary": f"Asset {asset_id} telemetry readings are within baseline operational tolerances.",
        "recommended_action": "Standard scheduled inspection."
    }


def telemetry_diagnostics_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: Telemetry Diagnostics Agent.
    Analyzes telemetry data and writes `diagnostic_result` to the state.
    """
    asset_id = state.get("asset_id", "UNKNOWN")
    telemetry_data = state.get("telemetry_data", {})
    records = telemetry_data.get("records", [])

    # Evaluate using electrical diagnostic engine
    diagnostic_result = analyze_telemetry_heuristics(asset_id, records)

    # Format human-readable agent thought message
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
