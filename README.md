# Industrial Multi-Agent Predictive Maintenance System ⚡

[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-blue.svg)](https://github.com/langchain-ai/langgraph)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-green.svg)](https://www.sqlite.org/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/Execution-100%25%20Local%20%26%20Zero--Cost-brightgreen.svg)](#)

A 100% local, zero-cost multi-agent AI system built with **LangGraph** and **SQLite** to diagnose industrial electrical faults (**11kV Transformers, Motor Control Centers (MCC), and Variable Frequency VFDs**), query maintenance manuals, and automatically schedule work orders. Designed and architected to bridge heavy industrial electrical engineering with modern agentic AI workflows.

---

## 🚀 Quick Start (Zero Cloud Setup Required)

Clone the repository and run the entire pipeline locally:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/amareshdas3-eng/multiagent-predictive-maintenance.git
   cd multiagent-predictive-maintenance
   ```

2. **Set up virtual environment & install dependencies:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1    # On Windows
   # source .venv/bin/activate     # On Linux / macOS
   pip install -r requirements.txt
   ```

3. **Initialize local database with sample industrial telemetry:**
   ```bash
   python seed_data.py
   ```

4. **Launch the interactive Streamlit Dashboard:**
   ```bash
   streamlit run app.py
   ```
   *(Or launch in 1 click on Windows with `run_app.bat` or run via CLI: `python main.py`)*

---

## 🧠 System Architecture & Agents

```
[ Industrial Telemetry ]
        │
        ▼
[ Telemetry Diagnostics Agent ] ──(Fault Detected?)──► [ Manual & RCA Retrieval Agent ]
                                                                  │
                                                                  ▼
                                                      [ Work Order Scheduler ] ──► [ SQLite DB ]
```

- **Telemetry Diagnostics Agent (`src/agents.py`)**: Analyzes thermal spikes, harmonic distortion (THD), and load imbalances based on industrial electrical principles:
  - **11kV Transformers**: Winding temperature spikes (>95°C alarm, >110°C trip per IEC 60076-11), fan failure, and phase unbalance (>10%).
  - **Motor Control Centers (MCC)**: Busbar thermal overload (>75°C alarm, >90°C trip per IEEE C37.20.1), frequent thermal relay trips, and contactor chatter signatures.
  - **Variable Frequency Drives (VFD)**: DC-link overvoltage (>740V trip), IGBT overtemperature (>95°C), high THD (>5% per IEEE 519), and output phase unbalance.
- **Manual & RCA Agent (`src/agents.py`)**: Queries local documentation and electrical engineering standards in SQLite (`MaintenanceManual` table), extracts OEM torque specs, Megger testing procedures, and life-critical safety warnings.
- **Scheduler Agent (`src/agents.py`)**: Evaluates severity against plant calendar windows, generates formal LOTO (Lockout/Tagout) requirements, assigns calibrated spares, and logs formal work orders into SQLite (`work_orders` table).

---

## 📁 Repository Structure

```
multiagent-predictive-maintenance/
├── data/
│   ├── equipment_manuals.json      # Sample OEM manuals / specs for 11kV Transformers, MCC, VFD
│   ├── equipment_metadata.json     # Technical ratings, LOTO points & location metadata
│   └── production_calendar.json    # Plant shifts, peak windows, and outage schedules
├── src/
│   ├── __init__.py
│   ├── database.py                 # SQLite setup & SQLAlchemy models
│   ├── agents.py                   # Telemetry, RCA, and Scheduler agent definitions
│   └── graph.py                    # LangGraph orchestration state machine
├── web/                            # Full-featured cyber-industrial web dashboard
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .gitignore                      # Ignore local dbs, virtual envs, and cache
├── requirements.txt                # Python dependencies
├── seed_data.py                    # Populates SQLite with sample industrial telemetry/assets
├── main.py                         # CLI runner script
├── app.py                          # Streamlit web UI runner
├── run_app.bat                     # 1-Click desktop launcher for Windows
├── test_pipeline.py                # Automated unit test suite (10/10 passing)
└── README.md                       # Professional documentation & portfolio showcase
```

---

## 💻 CLI Usage

```bash
# Run interactive CLI selection menu:
python main.py

# Diagnose specific equipment:
python main.py --asset TR-11kV-01      # 11kV Transformer Overheat & Fan Failure
python main.py --asset MCC-02          # MCC Busbar Thermal Overload & Chatter
python main.py --asset VFD-04          # 315kW VFD DC-Link Overvoltage & THD
python main.py --asset TR-11kV-NORMAL  # Healthy Baseline (Conditional Bypass Demo)

# Run all assets in batch:
python main.py --all
```

---

## 🧪 Automated Testing

Run the automated test suite verifying database operations, heuristic algorithms, manual retrieval, and LangGraph conditional branches:

```bash
python -m unittest test_pipeline.py
```

Expected output:
```
Ran 10 tests in 0.061s
OK
```

---

## 🛡️ Industrial Engineering Standards Referenced
- **IEC 60076-11**: Dry-Type Power Transformers (Class F temperature rise limits, Megger insulation resistance testing).
- **IEEE C37.20.1**: Metal-Enclosed Low-Voltage Switchgear and Busway Systems.
- **IEEE 141**: Recommended Practice for Electric Power Distribution in Industrial Plants (Red Book).
- **IEEE 519**: Standard for Harmonic Control in Electric Power Systems.
- **NFPA 70E**: Standard for Electrical Safety in the Workplace (Lockout / Tagout & Arc Flash Category 4).

---

## 👨‍💻 About the Author

**Amaresh Das**  
*Senior Industrial Project, Reliability & AI Transformation Consultant*  
23+ years of experience in heavy electrical infrastructure, substation commissioning, and industrial project controls.  
[LinkedIn Profile](https://linkedin.com/in/YOUR_LINKEDIN) | [ProEngineering Portfolio](https://proengineering.in)
