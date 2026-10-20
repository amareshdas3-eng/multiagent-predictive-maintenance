"""
graph.py - LangGraph State Machine Orchestration for Multi-Agent Predictive Maintenance.

Orchestrates the predictive maintenance pipeline across heavy industrial electrical assets:
1. START -> telemetry_diagnostics_node
2. telemetry_diagnostics_node -> conditional check:
      if fault_detected == True -> manual_retrieval_node
      else -> END
3. manual_retrieval_node -> work_order_scheduler_node
4. work_order_scheduler_node -> END
"""

import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from database import fetch_latest_telemetry, init_db
from agents.telemetry_diagnostics import telemetry_diagnostics_agent
from agents.manual_retrieval import manual_retrieval_agent
from agents.work_order_scheduler import work_order_scheduler_agent


class AgentState(TypedDict):
    """
    Central shared state object traversing the LangGraph state machine.
    """
    asset_id: str
    telemetry_data: dict
    diagnostic_result: dict
    manual_guidelines: dict
    work_order: str
    messages: list


def check_fault_condition(state: AgentState) -> str:
    """
    Conditional edge router:
    If a fault is detected by the Telemetry Diagnostics Agent, route to RCA and manual retrieval.
    If the asset is operating normally, branch directly to END to save resources.
    """
    diagnostic = state.get("diagnostic_result", {})
    fault_detected = diagnostic.get("fault_detected", False)
    if fault_detected:
        return "manual_retrieval_node"
    return END


def create_predictive_maintenance_graph():
    """
    Constructs and compiles the StateGraph workflow.
    """
    workflow = StateGraph(AgentState)

    # Register agent nodes
    workflow.add_node("telemetry_diagnostics_node", telemetry_diagnostics_agent)
    workflow.add_node("manual_retrieval_node", manual_retrieval_agent)
    workflow.add_node("work_order_scheduler_node", work_order_scheduler_agent)

    # Edge: START -> Telemetry Diagnostics
    workflow.add_edge(START, "telemetry_diagnostics_node")

    # Conditional Branch: Telemetry Diagnostics -> Manual Retrieval OR END
    workflow.add_conditional_edges(
        "telemetry_diagnostics_node",
        check_fault_condition,
        {
            "manual_retrieval_node": "manual_retrieval_node",
            END: END
        }
    )

    # Edge: Manual Retrieval -> Work Order Scheduler
    workflow.add_edge("manual_retrieval_node", "work_order_scheduler_node")

    # Edge: Work Order Scheduler -> END
    workflow.add_edge("work_order_scheduler_node", END)

    # Compile the graph
    app = workflow.compile()
    return app


# Pre-compiled application graph instance
maintenance_graph = create_predictive_maintenance_graph()


def run_pipeline(asset_id: str, custom_telemetry: Optional[List[dict]] = None) -> AgentState:
    """
    Executes the multi-agent predictive maintenance pipeline for a given asset.
    Loads real-time telemetry from SQLite database if not provided directly.
    """
    # Retrieve telemetry records from SQLite database layer
    if custom_telemetry is None:
        records = fetch_latest_telemetry(asset_id, limit=50)
    else:
        records = custom_telemetry

    initial_state: AgentState = {
        "asset_id": asset_id,
        "telemetry_data": {
            "asset_id": asset_id,
            "count": len(records),
            "records": records
        },
        "diagnostic_result": {},
        "manual_guidelines": {},
        "work_order": "",
        "messages": []
    }

    # Execute graph through LangGraph state machine
    final_state = maintenance_graph.invoke(initial_state)
    return final_state
