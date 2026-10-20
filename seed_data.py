"""
seed_data.py - Seeds the SQLite database with realistic heavy electrical industrial data.

Populates:
1. TelemetryRecord: Realistic sensor windows for 11kV Transformers, MCCs, and VFDs.
2. MaintenanceManual: Chunked engineering standards (IEC 60076, IEEE C37.20.1, VFD OEM guides).
"""

import os
from datetime import datetime, timezone, timedelta
from database import init_db, get_db_session, TelemetryRecord, MaintenanceManual, WorkOrder

def seed_database():
    print("[*] Initializing SQLite database schema...")
    init_db()
    session = get_db_session()

    try:
        # Clear existing tables for fresh seed
        session.query(TelemetryRecord).delete()
        session.query(MaintenanceManual).delete()
        session.query(WorkOrder).delete()
        session.commit()
        print("[+] Existing records cleared.")

        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # 1. Telemetry Records for Heavy Electrical Equipment
        # -------------------------------------------------------------
        telemetry_items = []

        # --- A. 11kV Dry-Type Transformer: TR-11kV-01 (FAULTY SCENARIO) ---
        # Fault: Winding temp spike (114.5°C > 110°C trip), cooling fan failure, phase load asymmetry
        base_time = now - timedelta(minutes=45)
        for i in range(10):
            t = base_time + timedelta(minutes=i * 5)
            # Winding temp ramps up from 96°C to 114.5°C
            w_temp = 96.0 + (i * 2.1)
            telemetry_items.extend([
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="winding_temp", value=round(w_temp, 2), unit="°C", status="CRITICAL" if w_temp >= 110 else "WARNING"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="cooling_fan_status", value=0.0, unit="state (0=FAULT, 1=RUN)", status="CRITICAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="cooling_fan_rpm", value=0.0, unit="RPM", status="CRITICAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="load_current_phase_a", value=142.5, unit="Amps", status="WARNING"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="load_current_phase_b", value=92.1, unit="Amps", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="load_current_phase_c", value=88.4, unit="Amps", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="vibration_mm_s", value=3.8, unit="mm/s", status="WARNING"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-01", parameter_name="ambient_temp", value=38.2, unit="°C", status="NORMAL")
            ])

        # --- B. Motor Control Center: MCC-02 (FAULTY SCENARIO) ---
        # Fault: Busbar thermal overload (88.4°C > 75°C alarm), contactor chatter, high thermal relay trips
        for i in range(10):
            t = base_time + timedelta(minutes=i * 5)
            b_temp = 82.0 + (i * 0.7)
            telemetry_items.extend([
                TelemetryRecord(timestamp=t, asset_id="MCC-02", parameter_name="busbar_temperature", value=round(b_temp, 2), unit="°C", status="CRITICAL" if b_temp >= 85 else "WARNING"),
                TelemetryRecord(timestamp=t, asset_id="MCC-02", parameter_name="contactor_chatter_events_hr", value=18.0, unit="events/hr", status="CRITICAL"),
                TelemetryRecord(timestamp=t, asset_id="MCC-02", parameter_name="control_coil_voltage", value=86.5, unit="Volts AC", status="WARNING"),  # Under-voltage causing chatter!
                TelemetryRecord(timestamp=t, asset_id="MCC-02", parameter_name="thermal_relay_trip_count", value=4.0, unit="trips/shift", status="CRITICAL"),
                TelemetryRecord(timestamp=t, asset_id="MCC-02", parameter_name="load_current_amps", value=2890.0, unit="Amps", status="WARNING"),
                TelemetryRecord(timestamp=t, asset_id="MCC-02", parameter_name="phase_voltage_imbalance", value=4.2, unit="%", status="WARNING")
            ])

        # --- C. Variable Frequency Drive: VFD-04 (FAULTY SCENARIO) ---
        # Fault: DC-link overvoltage (764V > 740V trip), IGBT overtemperature (99.2°C), high THD (14.8%)
        for i in range(10):
            t = base_time + timedelta(minutes=i * 5)
            dc_v = 710.0 + (i * 6.0)
            igbt_t = 88.0 + (i * 1.25)
            telemetry_items.extend([
                TelemetryRecord(timestamp=t, asset_id="VFD-04", parameter_name="dc_link_voltage", value=round(dc_v, 2), unit="Volts DC", status="CRITICAL" if dc_v >= 740 else "WARNING"),
                TelemetryRecord(timestamp=t, asset_id="VFD-04", parameter_name="igbt_temperature", value=round(igbt_t, 2), unit="°C", status="CRITICAL" if igbt_t >= 95 else "WARNING"),
                TelemetryRecord(timestamp=t, asset_id="VFD-04", parameter_name="harmonic_distortion", value=14.8, unit="% THD", status="CRITICAL"),
                TelemetryRecord(timestamp=t, asset_id="VFD-04", parameter_name="output_phase_imbalance", value=8.6, unit="%", status="WARNING"),
                TelemetryRecord(timestamp=t, asset_id="VFD-04", parameter_name="heatsink_fan_rpm", value=620.0, unit="RPM", status="WARNING")  # Fan choked
            ])

        # --- D. Baseline Healthy Equipment: TR-11kV-NORMAL ---
        for i in range(10):
            t = base_time + timedelta(minutes=i * 5)
            telemetry_items.extend([
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-NORMAL", parameter_name="winding_temp", value=68.5, unit="°C", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-NORMAL", parameter_name="cooling_fan_status", value=1.0, unit="state", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-NORMAL", parameter_name="cooling_fan_rpm", value=1450.0, unit="RPM", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-NORMAL", parameter_name="load_current_phase_a", value=95.0, unit="Amps", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-NORMAL", parameter_name="load_current_phase_b", value=94.2, unit="Amps", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-NORMAL", parameter_name="load_current_phase_c", value=95.1, unit="Amps", status="NORMAL"),
                TelemetryRecord(timestamp=t, asset_id="TR-11kV-NORMAL", parameter_name="vibration_mm_s", value=1.1, unit="mm/s", status="NORMAL")
            ])

        session.bulk_save_objects(telemetry_items)
        session.commit()
        print(f"[+] Inserted {len(telemetry_items)} telemetry sensor records.")

        # -------------------------------------------------------------
        # 2. Maintenance Manuals and Engineering Standards Chunks
        # -------------------------------------------------------------
        manual_chunks = [
            # --- IEC 60076 (Transformers) ---
            MaintenanceManual(
                doc_id="MAN-TR-01",
                asset_type="Transformer",
                title="IEC 60076-11 Power Transformers: Dry-Type Operational Limits & Thermal Protection",
                section="Section 8.2: Winding Temperature Rise & Cooling Failure Diagnostics",
                content_chunk=(
                    "Dry-type cast-resin transformers with Class F insulation have a maximum rated temperature limit "
                    "of 155°C and an allowable temperature rise of 100K above ambient (40°C). "
                    "Alarm threshold is set at 95°C and automatic emergency trip threshold is mandated at 110°C. "
                    "Root cause for sudden thermal gradient spikes (>1.5°C/min): "
                    "1. Forced cooling cross-flow fan blower failure, stalled motor, or blown motor fuse. "
                    "2. Severe phase load current asymmetry (>10% unbalance) creating localized hot-spot winding flux saturation. "
                    "3. Air intake louvers obstructed by dust accretion or foreign objects. "
                    "IMMEDIATE ACTION: If winding temp exceeds 110°C, transfer critical loads to redundant transformer bus "
                    "or initiate controlled shedding within 15 minutes."
                )
            ),
            MaintenanceManual(
                doc_id="MAN-TR-02",
                asset_type="Transformer",
                title="IEC 60076-11 Testing Procedures & Insulation Resistance Protocol",
                section="Section 14.3: Post-Fault Insulation Resistance (Megger) & Busbar Torque Specs",
                content_chunk=(
                    "Mandatory post-overheat inspection procedure for 11kV dry-type transformers: "
                    "1. Isolate and ground both HV (11kV) and LV (415V) terminals. "
                    "2. Perform Insulation Resistance (IR) test using a calibrated 5kV motorized Megger for HV windings: "
                    "Minimum acceptable value R_1min is 1000 Megohms at 20°C. LV winding test with 1kV Megger (min 100 MΩ). "
                    "3. Polarization Index (PI = R_10min / R_1min) must be >= 2.0. "
                    "4. Mechanical Busbar Torque Specs: High-tensile grade 8.8 bolts for HV terminations (M12) must be torqued "
                    "to exactly 85 Nm; LV copper flexible links (M16) must be torqued to 120 Nm using a certified torque wrench. "
                    "5. Check cooling fan auxiliary contactor coil supply and replace blown 24VDC/230VAC fan control relays."
                )
            ),
            MaintenanceManual(
                doc_id="MAN-TR-03",
                asset_type="Transformer",
                title="Substation Dry-Type Transformer Maintenance SOP & Airflow Clearance",
                section="Section 4.1: Cooling Fan Blower Assembly Replacement and Airway Clearances",
                content_chunk=(
                    "Air Forced (AF) cooling booster systems utilize tangential fan blowers mounted below each resin coil. "
                    "If fan status indicates 0 RPM while temperature is > 85°C: "
                    "Check PT100 temperature sensor controller loop resistance (nominal 138.5 Ω at 100°C). "
                    "Inspect blower impeller bearings for seizure or thermal binding. "
                    "Spares Required: Part #FAN-TR-2500KVA tangential blower motor assembly, PT100 3-wire RTD sensor probe, "
                    "replacement control fuse 6A type gG. Clean cooling ducts using compressed dry nitrogen (< 2 bar)."
                )
            ),

            # --- IEEE C37.20.1 & IEEE 141 (MCCs) ---
            MaintenanceManual(
                doc_id="MAN-MCC-01",
                asset_type="MCC",
                title="IEEE C37.20.1 Metal-Enclosed Switchgear & Busway Thermal Overload Standards",
                section="Section 6.4: Busbar Temperature Rise Criteria and Thermal Relay Tripping",
                content_chunk=(
                    "In 415V 3200A Motor Control Centers (MCC), busbar joint temperatures must not exceed 75°C under normal "
                    "continuous duty (maximum allowable temperature limit 90°C under full load). "
                    "Thermographic inspection revealing delta-T > 15°C across adjacent phase joints indicates loose Belleville washers, "
                    "severe harmonic heating, or galvanic oxidation. "
                    "Frequent thermal relay tripping (>2 events/shift) signifies improper bi-metallic relay calibration, "
                    "elevated ambient enclosure temperatures (>50°C), or sustained motor stall currents. "
                    "Inspect ventilation fan intake filters and check breaker thermal-magnetic trip unit dial settings."
                )
            ),
            MaintenanceManual(
                doc_id="MAN-MCC-02",
                asset_type="MCC",
                title="IEEE 141 Recommended Practice for Industrial Electric Power Systems: Contactor Diagnostics",
                section="Section 9.5: Contactor Chatter Root Cause Analysis & Control Circuit Under-voltage",
                content_chunk=(
                    "Contactor chatter (rapid oscillation/bouncing of armature contacts) causes severe contact erosion, "
                    "micro-arcing, and catastrophic contact welding. "
                    "Primary root cause is control circuit under-voltage: When AC control voltage drops below 85% of rated "
                    "(e.g., <93.5V on a 110VAC nominal bus or <187V on 220VAC), magnetic holding flux collapses intermittently. "
                    "Secondary causes: Shading coil crack or fracture in laminated magnet assembly, excessive mechanical dust "
                    "preventing complete armature seating, or auxiliary interlock contact bounce. "
                    "Action: Measure control transformer secondary voltage under inrush load; inspect contact tip wear; "
                    "verify secondary injection relay timings using OMICRON or secondary test set."
                )
            ),
            MaintenanceManual(
                doc_id="MAN-MCC-03",
                asset_type="MCC",
                title="MCC Maintenance SOP: Bolted Joint Torque & Secondary Injection Testing",
                section="Section 11.2: Joint Retorque, Shading Coil Replacement and Bus Stabs",
                content_chunk=(
                    "Maintenance crew procedures for MCC busbar and contactor overhaul: "
                    "1. Isolate upstream incoming breaker and execute full Lockout/Tagout (LOTO). "
                    "2. Retorque all Cu/Al busbar splice plates using calibrated torque wrench: M10 grade 8.8 bolts = 45 Nm, "
                    "M12 bolts = 75 Nm. Apply torque seal inspection lacquer. "
                    "3. Disassemble contactor arc chutes; measure contact wipe and gap against OEM gauge (min 3.2 mm gap). "
                    "Replace contactor coil assembly if DC resistance deviates >10% from nominal. "
                    "4. Perform micro-ohmmeter (Ductor) test across main busbar joints: Joint resistance must be < 15 micro-ohms."
                )
            ),

            # --- Heavy Industrial VFD (Drives) ---
            MaintenanceManual(
                doc_id="MAN-VFD-01",
                asset_type="VFD",
                title="OEM 315kW Heavy Industrial Variable Frequency Drive Troubleshooting Manual",
                section="Section 5.1: DC-Link Overvoltage & Regenerative Braking Faults",
                content_chunk=(
                    "The nominal DC-bus voltage for a 415V/690V industrial VFD is 1.35 * V_line (~560V-585V DC). "
                    "The overvoltage warning threshold is 720V DC and emergency overvoltage trip occurs at 740V DC. "
                    "Root Causes of DC-Link Overvoltage: "
                    "1. High inertia pump deceleration regeneration without dynamic braking resistor (DBR) or active regenerative front end. "
                    "2. Severe utility line voltage transients, capacitor bank switching on 11kV bus. "
                    "3. Defective DC-bus voltage sensing feedback divider board or optical isolation failure. "
                    "Action: Verify dynamic braking chopper IGBT firing pulse and check DBR resistor bank continuity."
                )
            ),
            MaintenanceManual(
                doc_id="MAN-VFD-02",
                asset_type="VFD",
                title="OEM VFD Power Module Guidelines: IGBT Overtemperature & Harmonic Mitigation",
                section="Section 7.3: IGBT Thermal Dissipation, Heat Sink Aerodynamics & IEEE 519 THD",
                content_chunk=(
                    "IGBT junction temperatures must stay below 85°C for maximum semiconductor longevity (absolute trip at 95°C). "
                    "If IGBT thermal sensors report rapid heating while motor current is within rated envelope: "
                    "1. Internal heatsink cooling fan tachometer failure or blocked aluminum heatsink fins. "
                    "2. Degraded thermal interface paste (TIM) between IGBT power module baseplate and heatsink. "
                    "3. Excessive harmonic distortion (THD > 5% as per IEEE 519): 5th and 7th harmonic current circulation "
                    "causes core eddy-current heating and inverter bridge skin effect losses. "
                    "Action: Clean heatsink with ESD-safe vacuum, inspect cooling fan capacitor, check line reactor (3% or 5% impedance)."
                )
            ),
            MaintenanceManual(
                doc_id="MAN-VFD-03",
                asset_type="VFD",
                title="Industrial VFD Safety SOP: DC Bus Stored Energy Discharge Protocol",
                section="Section 2.4: Life-Critical Capacitive Energy Discharge and LOTO Procedure",
                content_chunk=(
                    "DANGER - LETHAL STORED VOLTAGE: The DC capacitor bank in 315kW VFDs stores over 800 Joules of lethal energy. "
                    "Turning off the input AC breaker DOES NOT immediately remove DC bus voltage. "
                    "MANDATORY SAFETY STEPS: "
                    "1. Lock out and tag out incoming breaker MCC-02-F08. "
                    "2. Wait at least 10 MINUTES for internal bleeder resistors to discharge the capacitors. "
                    "3. Before touching any terminals, wear Class 0 (1000V) electrical insulating gloves and face shield. "
                    "4. Measure DC-link voltage between terminals DC+ and DC- using a certified CAT IV 1000V multimeter. "
                    "Ensure voltage is CONFIRMED BELOW 50V DC before beginning work. "
                    "5. Measure phase-to-ground voltage on all output terminals U, V, W."
                )
            )
        ]

        session.bulk_save_objects(manual_chunks)
        session.commit()
        print(f"[+] Inserted {len(manual_chunks)} maintenance manual and standard chunks.")
        print("[+] Database seeding completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"[!] Error seeding database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
