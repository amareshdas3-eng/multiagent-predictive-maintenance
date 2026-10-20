"""
main.py - Self-Contained Recruiter-Friendly CLI for Multi-Agent Predictive Maintenance.

Heavy Electrical Assets:
- 11kV Dry-Type Transformers
- Motor Control Centers (MCC)
- Industrial Variable Frequency Drives (VFD)

Run locally:
    python main.py
    python main.py --asset TR-11kV-01
    python main.py --asset MCC-02
    python main.py --asset VFD-04
    python main.py --asset TR-11kV-NORMAL
    python main.py --all
"""

import sys
import os
import argparse
import time

# Ensure Windows terminal handles UTF-8 gracefully
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from database import DB_PATH, init_db, get_db_session, TelemetryRecord
from seed_data import seed_database
from graph import run_pipeline

# ANSI Color Codes for Recruiter-Friendly Terminal Visuals
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


BANNER = f"""{CYAN}{BOLD}
========================================================================================
     MULTI-AGENT PREDICTIVE MAINTENANCE: HEAVY ELECTRICAL ASSETS
========================================================================================
  Specialized Industrial Power Systems Pipeline powered by LangGraph & SQLite
  - 11kV / 415V Cast-Resin Transformers (IEC 60076-11)
  - 415V 3200A Motor Control Centers (IEEE C37.20.1 / IEEE 141)
  - 315kW Heavy Industrial Variable Frequency Drives (PWM Inverters)
========================================================================================{RESET}
"""

SAMPLE_ASSETS = [
    {
        "id": "TR-11kV-01",
        "name": "11kV / 415V Dry-Type Transformer 1A (Substation-A)",
        "condition": "FAULTY: Thermal Overload (>110°C Trip), Fan Failure, Current Asymmetry",
        "type": "Transformer"
    },
    {
        "id": "MCC-02",
        "name": "Boiler MCC 02 Incomer & Busway (3200A 415V)",
        "condition": "FAULTY: Busbar Overheating (88.4°C), Contactor Chatter, Relay Trips",
        "type": "MCC"
    },
    {
        "id": "VFD-04",
        "name": "Feed Pump VFD 04 (315kW Industrial Drive)",
        "condition": "FAULTY: DC-Link Overvoltage (764V), IGBT Overheat, 14.8% THD",
        "type": "VFD"
    },
    {
        "id": "TR-11kV-NORMAL",
        "name": "11kV Auxiliary Transformer 1B (Substation-B)",
        "condition": "HEALTHY: Baseline Operations (Demonstrates Conditional Early Exit to END)",
        "type": "Transformer"
    }
]


def ensure_database_ready():
    """Auto-seeds database if not found or empty."""
    if not os.path.exists(DB_PATH):
        print(f"{YELLOW}[!] Local SQLite database not found. Initializing and seeding...{RESET}")
        seed_database()
        return

    session = get_db_session()
    try:
        count = session.query(TelemetryRecord).count()
        if count == 0:
            print(f"{YELLOW}[!] Database is empty. Seeding realistic sample telemetry...{RESET}")
            seed_database()
    finally:
        session.close()


def print_divider(title: str = ""):
    line = "=" * 80
    if title:
        print(f"\n{CYAN}{BOLD}{line}\n  {title}\n{line}{RESET}")
    else:
        print(f"{DIM}{line}{RESET}")


def execute_asset_pipeline(asset_id: str):
    """Executes the LangGraph state machine and prints formatted step-by-step agent interactions."""
    print(f"\n{BOLD}{YELLOW}>>> Initiating Predictive Maintenance Pipeline for Asset: [{asset_id}]...{RESET}\n")
    time.sleep(0.3)

    final_state = run_pipeline(asset_id)

    # 1. Output Telemetry Diagnostics Agent
    diagnostic = final_state.get("diagnostic_result", {})
    fault_detected = diagnostic.get("fault_detected", False)
    severity = diagnostic.get("severity", "Low")

    severity_color = RED if severity == "Critical" else (YELLOW if severity == "High" else GREEN)

    print(f"{CYAN}{BOLD}[NODE 1: Telemetry Diagnostics Agent]{RESET}")
    print(f"  Target Asset:     {BOLD}{asset_id}{RESET}")
    print(f"  Fault Detected:   {RED if fault_detected else GREEN}{BOLD}{fault_detected}{RESET}")
    print(f"  Fault Category:   {YELLOW}{diagnostic.get('fault_category', 'None')}{RESET}")
    print(f"  Fault Severity:   {severity_color}{BOLD}{severity.upper()}{RESET}")
    print(f"  Diagnostic Summary:\n    {DIM}{diagnostic.get('diagnostic_summary')}{RESET}")
    print(f"  Recommended Action:\n    {GREEN}{diagnostic.get('recommended_action')}{RESET}\n")

    # 2. Output Conditional Router Decision
    print(f"{CYAN}{BOLD}[CONDITIONAL ROUTING DECISION]{RESET}")
    if fault_detected:
        print(f"  -> Decision: {RED}FAULT DETECTED ({severity}){RESET}. Routing to {BOLD}manual_retrieval_node{RESET}...")
    else:
        print(f"  -> Decision: {GREEN}EQUIPMENT HEALTHY{RESET}. Conditional edge bypassing RCA and routing to {BOLD}END{RESET}.")
        print_divider("PIPELINE COMPLETED - NO ACTION REQUIRED")
        return

    # 3. Output Manual Retrieval & RCA Agent
    manual_data = final_state.get("manual_guidelines", {})
    refs = manual_data.get("referenced_manuals", [])
    print(f"\n{CYAN}{BOLD}[NODE 2: Manual Retrieval & Root Cause Analysis Agent]{RESET}")
    print(f"  Asset Classification: {BOLD}{manual_data.get('asset_type')}{RESET}")
    print(f"  Referenced Engineering Standards & OEM Chunks:")
    for r in refs:
        print(f"    - {BOLD}{r}{RESET}")
    print(f"\n  Safety Warnings:\n    {RED}{BOLD}{manual_data.get('safety_warnings')}{RESET}\n")

    # 4. Output Work Order & Scheduler Agent
    work_order_text = final_state.get("work_order", "")
    print(f"{CYAN}{BOLD}[NODE 3: Work Order & Maintenance Scheduler Agent]{RESET}")
    print(f"  Priority Level:       {severity_color}{BOLD}{severity.upper()}{RESET}")
    print(f"  Status:               {GREEN}WORK ORDER GENERATED & COMMITTED TO SQLITE{RESET}")
    print(f"  Target Database:      {DB_PATH} (Table: 'work_orders')\n")

    print_divider("FORMAL WORK ORDER DOCUMENT")
    print(work_order_text)
    print_divider("PIPELINE EXECUTION COMPLETED")


def main():
    print(BANNER)
    ensure_database_ready()

    parser = argparse.ArgumentParser(description="Multi-Agent Predictive Maintenance for Heavy Electrical Assets")
    parser.add_argument("--asset", type=str, help="Asset ID to diagnose (e.g., TR-11kV-01, MCC-02, VFD-04, TR-11kV-NORMAL)")
    parser.add_argument("--all", action="store_true", help="Run the diagnostic pipeline sequentially for all sample assets")
    parser.add_argument("--reseed", action="store_true", help="Re-seed SQLite database with fresh initial telemetry")
    parser.add_argument("--web", action="store_true", help="Launch the interactive web application dashboard")

    args = parser.parse_args()

    if args.web:
        import subprocess
        print(f"{CYAN}{BOLD}[*] Launching Interactive Web Application...{RESET}")
        subprocess.run([sys.executable, "app.py"])
        return

    if args.reseed:
        seed_database()
        if not args.asset and not args.all:
            return

    if args.all:
        for asset in SAMPLE_ASSETS:
            execute_asset_pipeline(asset["id"])
            time.sleep(0.5)
        return

    if args.asset:
        execute_asset_pipeline(args.asset)
        return

    # Interactive Menu Selection
    print(f"{BOLD}Select an Electrical Asset to Run Predictive Diagnostics:{RESET}\n")
    for idx, asset in enumerate(SAMPLE_ASSETS, 1):
        print(f"  [{idx}] {BOLD}{asset['id']:<16}{RESET} : {asset['name']}")
        print(f"      {DIM}{asset['condition']}{RESET}\n")
    print(f"  [5] {BOLD}RUN ALL ASSETS SEQUENTIALLY{RESET}")
    print(f"  [6] {BOLD}RE-SEED SQLITE DATABASE{RESET}")
    print(f"  [7] {BOLD}LAUNCH INTERACTIVE WEB APPLICATION (1-CLICK GUI){RESET}")
    print(f"  [0] {BOLD}EXIT{RESET}\n")

    try:
        choice = input(f"{BOLD}Enter selection (0-7) [default: 1]: {RESET}").strip()
        if not choice:
            choice = "1"

        if choice == "0":
            print("Exiting.")
            sys.exit(0)
        elif choice in ["1", "2", "3", "4"]:
            selected = SAMPLE_ASSETS[int(choice) - 1]
            execute_asset_pipeline(selected["id"])
        elif choice == "5":
            for asset in SAMPLE_ASSETS:
                execute_asset_pipeline(asset["id"])
                time.sleep(0.4)
        elif choice == "6":
            seed_database()
        elif choice == "7":
            import subprocess
            print(f"{CYAN}{BOLD}[*] Launching Interactive Web Application...{RESET}")
            subprocess.run([sys.executable, "app.py"])
        else:
            print(f"{RED}Invalid selection. Running default asset TR-11kV-01...{RESET}")
            execute_asset_pipeline("TR-11kV-01")

    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
