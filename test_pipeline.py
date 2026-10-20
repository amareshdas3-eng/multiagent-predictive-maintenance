"""
test_pipeline.py - Automated Test Suite for Multi-Agent Predictive Maintenance System.
Tests:
1. Database operations and SQLAlchemy models.
2. Telemetry Diagnostics Agent anomaly detection.
3. Manual Retrieval and RCA Agent chunk indexing.
4. Work Order Scheduler and SQLite persistence.
5. LangGraph state machine routing (both fault and healthy paths).
"""

import unittest
import os
from database import (
    init_db,
    get_db_session,
    fetch_latest_telemetry,
    search_manuals,
    TelemetryRecord,
    MaintenanceManual,
    WorkOrder,
    save_work_order
)
from seed_data import seed_database
from agents.telemetry_diagnostics import analyze_telemetry_heuristics, telemetry_diagnostics_agent
from agents.manual_retrieval import manual_retrieval_agent
from agents.work_order_scheduler import work_order_scheduler_agent
from graph import run_pipeline, check_fault_condition, AgentState
from langgraph.graph import END


class TestPredictiveMaintenanceSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure clean database seeding before running tests."""
        seed_database()

    def test_01_database_records_exist(self):
        """Verify seeded telemetry and manual records exist in SQLite."""
        session = get_db_session()
        try:
            telemetry_count = session.query(TelemetryRecord).count()
            manual_count = session.query(MaintenanceManual).count()
            self.assertGreater(telemetry_count, 100, "Should have seeded telemetry records")
            self.assertGreaterEqual(manual_count, 9, "Should have seeded 9 maintenance manual chunks")
        finally:
            session.close()

    def test_02_transformer_fault_diagnostics(self):
        """Test 11kV transformer overtemperature and fan failure detection."""
        records = fetch_latest_telemetry("TR-11kV-01")
        result = analyze_telemetry_heuristics("TR-11kV-01", records)
        self.assertTrue(result["fault_detected"])
        self.assertEqual(result["severity"], "Critical")
        self.assertIn("Thermal Overload", result["fault_category"])
        self.assertIn("IEC 60076-11", result["diagnostic_summary"])

    def test_03_mcc_fault_diagnostics(self):
        """Test Motor Control Center busbar heating and contactor chatter."""
        records = fetch_latest_telemetry("MCC-02")
        result = analyze_telemetry_heuristics("MCC-02", records)
        self.assertTrue(result["fault_detected"])
        self.assertIn(result["severity"], ["Critical", "High"])
        self.assertIn("Busbar", result["fault_category"])

    def test_04_vfd_fault_diagnostics(self):
        """Test VFD DC-link overvoltage, IGBT temp, and harmonic distortion."""
        records = fetch_latest_telemetry("VFD-04")
        result = analyze_telemetry_heuristics("VFD-04", records)
        self.assertTrue(result["fault_detected"])
        self.assertEqual(result["severity"], "Critical")
        self.assertIn("DC-Link Overvoltage", result["fault_category"])

    def test_05_healthy_asset_baseline(self):
        """Test that healthy asset does NOT flag faults."""
        records = fetch_latest_telemetry("TR-11kV-NORMAL")
        result = analyze_telemetry_heuristics("TR-11kV-NORMAL", records)
        self.assertFalse(result["fault_detected"])
        self.assertEqual(result["severity"], "Low")

    def test_06_manual_retrieval(self):
        """Test manual retrieval agent finds relevant chunks."""
        state = {
            "asset_id": "TR-11kV-01",
            "diagnostic_result": {
                "fault_category": "Thermal Overload & Cooling Failure",
                "diagnostic_summary": "Winding temperature trip 114C cooling fan failure"
            },
            "messages": []
        }
        res_state = manual_retrieval_agent(state)
        guidelines = res_state["manual_guidelines"]
        self.assertEqual(guidelines["asset_type"], "Transformer")
        self.assertGreater(len(guidelines["referenced_manuals"]), 0)
        self.assertGreater(len(guidelines["troubleshooting_steps"]), 0)
        self.assertIn("11,000 VOLTS", guidelines["safety_warnings"])

    def test_07_work_order_persistence(self):
        """Test work order creation and SQLite persistence."""
        order_payload = {
            "order_id": "TEST-WO-9999",
            "asset_id": "VFD-04",
            "fault_detected": True,
            "priority": "Critical",
            "required_loto_steps": "- Test LOTO step 1\n- Test LOTO step 2",
            "scheduled_date": "2026-10-20 12:00 UTC",
            "status": "APPROVED",
            "summary": "DC Link Overvoltage"
        }
        saved = save_work_order(order_payload)
        self.assertEqual(saved.order_id, "TEST-WO-9999")

        session = get_db_session()
        try:
            query_res = session.query(WorkOrder).filter(WorkOrder.order_id == "TEST-WO-9999").first()
            self.assertIsNotNone(query_res)
            self.assertEqual(query_res.priority, "Critical")
        finally:
            session.close()

    def test_08_langgraph_conditional_branching(self):
        """Test that conditional routing directs faults to manual_retrieval_node and healthy to END."""
        faulty_state: AgentState = {
            "asset_id": "TR-11kV-01",
            "telemetry_data": {},
            "diagnostic_result": {"fault_detected": True},
            "manual_guidelines": {},
            "work_order": "",
            "messages": []
        }
        healthy_state: AgentState = {
            "asset_id": "TR-11kV-NORMAL",
            "telemetry_data": {},
            "diagnostic_result": {"fault_detected": False},
            "manual_guidelines": {},
            "work_order": "",
            "messages": []
        }
        self.assertEqual(check_fault_condition(faulty_state), "manual_retrieval_node")
        self.assertEqual(check_fault_condition(healthy_state), END)

    def test_09_full_pipeline_fault_path(self):
        """Test end-to-end execution of pipeline for faulty VFD."""
        final_state = run_pipeline("VFD-04")
        self.assertTrue(final_state["diagnostic_result"]["fault_detected"])
        self.assertGreater(len(final_state["work_order"]), 100)
        self.assertIn("WO-2026-VFD04", final_state["work_order"])

    def test_10_full_pipeline_healthy_path(self):
        """Test end-to-end execution of pipeline for healthy asset."""
        final_state = run_pipeline("TR-11kV-NORMAL")
        self.assertFalse(final_state["diagnostic_result"]["fault_detected"])
        # Should NOT have generated a work order because it exited early to END
        self.assertEqual(final_state["work_order"], "")


if __name__ == "__main__":
    unittest.main()
