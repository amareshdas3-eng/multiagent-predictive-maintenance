"""
app.py - Interactive Streamlit Application for Industrial Multi-Agent Predictive Maintenance.

Can be run via:
    streamlit run app.py
    python app.py
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# Allow running via `python app.py` directly by invoking Streamlit CLI
if __name__ == "__main__" and "streamlit" not in sys.modules and "--streamlit-child" not in sys.argv:
    try:
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", os.path.abspath(__file__), "--server.port=8501", "--server.headless=false"]
        sys.exit(stcli.main())
    except ImportError:
        pass

import streamlit as st
import pandas as pd

from src.database import init_db, get_db_session, fetch_latest_telemetry, WorkOrder
from src.graph import run_pipeline
from seed_data import seed_database

# Set page configuration
st.set_page_config(
    page_title="Industrial Multi-Agent Predictive Maintenance",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #070b14 0%, #0d1527 100%);
        border: 1px solid rgba(0, 240, 255, 0.25);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px -8px rgba(0, 0, 0, 0.6);
    }
    .main-header h1 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #f1f5f9;
        font-size: 1.8rem;
        margin: 0;
        font-weight: 700;
    }
    .main-header h1 span {
        color: #00f0ff;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .author-badge {
        display: inline-block;
        background: rgba(0, 240, 255, 0.1);
        border: 1px solid rgba(0, 240, 255, 0.3);
        color: #00f0ff;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 8px;
    }
    .agent-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #00f0ff;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .agent-box.rca {
        border-left-color: #8b5cf6;
    }
    .agent-box.sched {
        border-left-color: #10b981;
    }
</style>
""", unsafe_allow_html=True)

# Ensure database is initialized
init_db()

# App Header
st.markdown("""
<div class="main-header">
    <h1>⚡ INDUSTRIAL MULTI-AGENT <span>PREDICTIVE MAINTENANCE</span></h1>
    <p>Autonomous Edge AI for Heavy Industrial Power Assets: 11kV Transformers, Motor Control Centers (MCC), and VFD Drives</p>
    <div class="author-badge">Architected by Amaresh Das | 23+ Years Heavy Electrical Infrastructure & AI Integration</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://img.icons8.com/fluency/96/flash-on.png", width=64)
st.sidebar.title("Asset Configuration")
st.sidebar.markdown("**Select Electrical Asset:**")

ASSETS = {
    "TR-11kV-01": "11kV Transformer 1A (Thermal Overload & Fan Failure)",
    "MCC-02": "MCC-02 Incomer (Busbar Overheating & Contactor Chatter)",
    "VFD-04": "315kW Industrial VFD (DC-Link Overvoltage & THD Harmonics)",
    "TR-11kV-NORMAL": "11kV Transformer 1B (Healthy Baseline - Bypass Demo)"
}

selected_asset_id = st.sidebar.selectbox(
    "Target Equipment",
    options=list(ASSETS.keys()),
    format_func=lambda x: f"{x} - {ASSETS[x]}"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Local Data Operations")
if st.sidebar.button("🔄 Re-Seed SQLite Database"):
    seed_database()
    st.sidebar.success("Database reseeded with 260 telemetry records & OEM manual chunks!")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Engineering Standards Referenced:**
- **IEC 60076-11**: Dry-Type Power Transformers
- **IEEE C37.20.1**: Metal-Enclosed Switchgear
- **IEEE 141**: Industrial Power Systems
- **IEEE 519**: Harmonic Control Limits
- **NFPA 70E**: Electrical Workplace Safety & LOTO
""")

# Top Navigation Tabs
tab_diag, tab_sim, tab_history = st.tabs([
    "⚡ Autonomous Diagnostic Pipeline",
    "🎛️ Live Parameter Sensitivity Testing",
    "🗄️ SQLite Work Order Audit Trail"
])

# ------------------------------------------------------------------------------
# TAB 1: AUTONOMOUS DIAGNOSTIC PIPELINE
# ------------------------------------------------------------------------------
with tab_diag:
    col_info1, col_info2, col_info3 = st.columns([1, 1, 1])

    records = fetch_latest_telemetry(selected_asset_id, limit=6)
    with col_info1:
        st.metric(label="Target Asset ID", value=selected_asset_id)
    with col_info2:
        top_val = f"{records[0]['value']} {records[0]['unit']}" if records else "N/A"
        st.metric(label=f"Primary Sensor ({records[0]['parameter_name'] if records else ''})", value=top_val)
    with col_info3:
        status_flag = "⚠️ FAULT DETECTED" if "NORMAL" not in selected_asset_id else "✅ NOMINAL"
        st.metric(label="Expected Status", value=status_flag)

    st.markdown("### LangGraph Multi-Agent Orchestration Flow")
    flow_col1, flow_col2, flow_col3, flow_col4, flow_col5 = st.columns(5)
    with flow_col1:
        st.info("🚀 **START**\nTelemetry Ingest")
    with flow_col2:
        st.info("📊 **Agent 1**\nTelemetry Diagnostics")
    with flow_col3:
        st.warning("🔀 **Router Gate**\nFault Condition?")
    with flow_col4:
        st.info("📖 **Agent 2**\nManual & RCA Retrieval")
    with flow_col5:
        st.success("📝 **Agent 3**\nWork Order Scheduler")

    st.markdown("---")
    if st.button("⚡ Execute LangGraph Multi-Agent Pipeline", type="primary", use_container_width=True):
        with st.spinner(f"Running LangGraph agent coordination for {selected_asset_id}..."):
            start_time = time.time()
            final_state = run_pipeline(selected_asset_id)
            exec_time = round((time.time() - start_time) * 1000, 2)

        diag = final_state.get("diagnostic_result", {})
        has_fault = diag.get("fault_detected", False)
        severity = diag.get("severity", "Low")

        st.success(f"Pipeline executed in {exec_time} ms across all state machine nodes!")

        # Agent Thought Stream
        st.subheader("Agent Reasoning & Diagnostic Trace")
        messages = final_state.get("messages", [])
        for idx, msg in enumerate(messages, 1):
            role = msg.get("role", "")
            box_class = "rca" if "manual" in role else ("sched" if "scheduler" in role else "")
            st.markdown(f"""
            <div class="agent-box {box_class}">
                <strong>Node {idx}: {role.replace('_', ' ').title()}</strong><br>
                {msg.get('content', '').replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

        if not has_fault:
            st.balloons()
            st.info(f"✅ **Conditional Gate Decision:** Equipment {selected_asset_id} is operating safely. Router bypassed RCA and Scheduler, ending workflow early.")
        else:
            st.subheader("Generated Industrial Work Order (Committed to SQLite)")
            work_order_text = final_state.get("work_order", "")
            st.markdown(work_order_text)
            st.download_button(
                label="📥 Download Formal Work Order (Markdown)",
                data=work_order_text,
                file_name=f"WorkOrder_{selected_asset_id}.md",
                mime="text/markdown"
            )

# ------------------------------------------------------------------------------
# TAB 2: LIVE PARAMETER SENSITIVITY TESTING
# ------------------------------------------------------------------------------
with tab_sim:
    st.subheader("Real-Time Parameter Injection & Sensitivity Playground")
    st.markdown("Adjust physical sensor parameters live to test the exact mathematical trip boundaries configured in the agents:")

    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        sim_winding = st.slider("11kV Transformer Winding Temperature (°C)", min_value=40.0, max_value=140.0, value=114.5, step=0.5,
                                help="Alarm threshold: 95°C | Class F Trip Threshold: 110°C per IEC 60076-11")
        sim_busbar = st.slider("MCC Busbar Joint Temperature (°C)", min_value=30.0, max_value=110.0, value=88.4, step=0.5,
                               help="Alarm: 75°C | Maximum Withstand: 90°C per IEEE C37.20.1")
    with sim_col2:
        sim_dc_bus = st.slider("VFD DC-Link Voltage (V DC)", min_value=500.0, max_value=850.0, value=764.0, step=2.0,
                               help="Nominal: 565-650V | Emergency Overvoltage Trip: 740V")
        sim_thd = st.slider("Current Total Harmonic Distortion (THD %)", min_value=1.0, max_value=25.0, value=14.8, step=0.2,
                            help="IEEE 519 Recommended Maximum: 5.0% THD")

    if st.button("⚡ Inject Custom Telemetry & Execute Agent Pipeline", type="primary"):
        target_asset = "TR-11kV-01"
        if sim_dc_bus > 700:
            target_asset = "VFD-04"
        elif sim_busbar > 75:
            target_asset = "MCC-02"

        custom_telemetry = [
            {"parameter_name": "winding_temp", "value": sim_winding, "unit": "°C", "status": "SIMULATED"},
            {"parameter_name": "busbar_temperature", "value": sim_busbar, "unit": "°C", "status": "SIMULATED"},
            {"parameter_name": "dc_link_voltage", "value": sim_dc_bus, "unit": "V", "status": "SIMULATED"},
            {"parameter_name": "harmonic_distortion", "value": sim_thd, "unit": "%", "status": "SIMULATED"},
            {"parameter_name": "cooling_fan_status", "value": 0.0, "unit": "state", "status": "SIMULATED"}
        ]

        with st.spinner(f"Simulating custom telemetry on {target_asset}..."):
            sim_state = run_pipeline(target_asset, custom_telemetry=custom_telemetry)

        st.write(f"**Target Asset Selected for Injected Values:** `{target_asset}`")
        diag_res = sim_state.get("diagnostic_result", {})
        st.write(f"**Fault Detected:** `{diag_res.get('fault_detected')}` | **Severity:** `{diag_res.get('severity')}`")
        st.write(f"**Diagnostic Summary:** {diag_res.get('diagnostic_summary')}")

        if sim_state.get("work_order"):
            st.markdown("#### Generated Work Order:")
            st.markdown(sim_state.get("work_order"))

# ------------------------------------------------------------------------------
# TAB 3: SQLITE WORK ORDER AUDIT TRAIL
# ------------------------------------------------------------------------------
with tab_history:
    st.subheader("Persisted Work Orders Table (SQLite: plant_maintenance.db)")
    session = get_db_session()
    try:
        orders = session.query(WorkOrder).order_by(WorkOrder.created_at.desc()).all()
        if orders:
            order_data = [o.to_dict() for o in orders]
            df = pd.DataFrame(order_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No work orders recorded yet. Run a diagnostic on a faulty asset to generate one.")
    finally:
        session.close()

st.markdown("---")
st.caption("Industrial Multi-Agent Predictive Maintenance System • Built with LangGraph, SQLite, and Streamlit • 100% Local Execution")
