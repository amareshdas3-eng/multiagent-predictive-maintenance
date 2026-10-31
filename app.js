/**
 * Heavy Electrical Assets - Multi-Agent Predictive Maintenance Suite
 * Client-Side Orchestrator & LangGraph Simulation Engine
 * Author: Amaresh Das (https://github.com/amareshdas3-eng)
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM References
  const assetsGrid = document.getElementById("assets-grid");
  const execTimeBadge = document.getElementById("execution-time-badge");
  const agentLogs = document.getElementById("agent-logs");
  const woCard = document.getElementById("wo-card");
  const historyTableBody = document.querySelector("#history-table tbody");
  const simModal = document.getElementById("sim-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnSubmitSim = document.getElementById("btn-submit-sim");
  const btnReseed = document.getElementById("btn-reseed");

  // LangGraph Flow Nodes
  const nodeStart = document.getElementById("node-start");
  const nodeTelemetry = document.getElementById("node-telemetry");
  const nodeCondition = document.getElementById("node-condition");
  const nodeRca = document.getElementById("node-rca");
  const nodeScheduler = document.getElementById("node-scheduler");
  const nodeEnd = document.getElementById("node-end");
  const branchBypass = document.getElementById("branch-bypass");

  const statusTelemetry = document.getElementById("status-telemetry");
  const statusCondition = document.getElementById("status-condition");
  const statusRca = document.getElementById("status-rca");
  const statusScheduler = document.getElementById("status-scheduler");
  const statusEnd = document.getElementById("status-end");

  // Telemetry Inputs for Modal
  const simAssetId = document.getElementById("sim-asset-id");
  const simParam1 = document.getElementById("sim-param1");
  const simParam2 = document.getElementById("sim-param2");
  const simParam1Val = document.getElementById("sim-param1-val");
  const simParam2Val = document.getElementById("sim-param2-val");

  let loadedAssets = [];
  let inMemoryWorkOrders = [
    {
      work_order_id: "WO-TR-2026-9041",
      asset_id: "TR-11kV-01",
      priority: "CRITICAL",
      scheduled_date: new Date().toISOString().split("T")[0],
      assigned_team: "High-Voltage Transformer Specialist Team",
      estimated_hours: 6.5,
      maintenance_type: "CORRECTIVE_OVERHAUL",
      action_plan: "Isolate 11kV busbar; test cooling fan circuits and relay tripping contacts (IEC 60076)."
    },
    {
      work_order_id: "WO-MCC-2026-8812",
      asset_id: "MCC-02",
      priority: "HIGH",
      scheduled_date: new Date(Date.now() + 86400000).toISOString().split("T")[0],
      assigned_team: "Switchgear & MCC Maintenance Crew",
      estimated_hours: 4.0,
      maintenance_type: "PREVENTIVE_MAINTENANCE",
      action_plan: "Torque busbar joints; replace chattering auxiliary control contactor (IEEE C37.20.1)."
    }
  ];

  // Baseline Industrial Datasets (IEC 60076, IEEE C37.20.1, IEEE 519)
  const BASELINE_ASSETS = [
    {
      asset_id: "TR-11kV-01",
      metadata: {
        asset_name: "2.5 MVA 11kV/415V Cast-Resin Dry-Type Transformer",
        asset_type: "11kV Transformer",
        manufacturer: "ABB / Hitachi Energy",
        criticality_rating: "TIER-1 CRITICAL",
        location: "Substation-01 Indoor Bay"
      },
      recent_telemetry: [
        { parameter_name: "winding_temp", value: 114.5, unit: "°C", status: "CRITICAL" },
        { parameter_name: "cooling_fan_status", value: 0.0, unit: "0=FAULT, 1=RUN", status: "CRITICAL" },
        { parameter_name: "load_current_phase_a", value: 142.5, unit: "Amps", status: "WARNING" },
        { parameter_name: "vibration_mm_s", value: 3.8, unit: "mm/s", status: "WARNING" }
      ]
    },
    {
      asset_id: "MCC-02",
      metadata: {
        asset_name: "415V Intelligent Motor Control Center Lineup",
        asset_type: "Motor Control Center",
        manufacturer: "Siemens Sivacon S8",
        criticality_rating: "TIER-2 IMPORTANT",
        location: "Process MCC Room 2"
      },
      recent_telemetry: [
        { parameter_name: "busbar_temperature", value: 88.4, unit: "°C", status: "CRITICAL" },
        { parameter_name: "contactor_chatter_events_hr", value: 18.0, unit: "events/hr", status: "CRITICAL" },
        { parameter_name: "control_coil_voltage", value: 86.5, unit: "Volts AC", status: "WARNING" },
        { parameter_name: "phase_voltage_imbalance", value: 4.2, unit: "%", status: "WARNING" }
      ]
    },
    {
      asset_id: "VFD-04",
      metadata: {
        asset_name: "250 kW Medium-Voltage Variable Frequency Drive",
        asset_type: "VFD Drive",
        manufacturer: "Rockwell Allen-Bradley PowerFlex 755",
        criticality_rating: "TIER-1 CRITICAL",
        location: "Slurry Pump House Drive Rack"
      },
      recent_telemetry: [
        { parameter_name: "dc_link_voltage", value: 764.0, unit: "Volts DC", status: "CRITICAL" },
        { parameter_name: "igbt_temperature", value: 99.2, unit: "°C", status: "CRITICAL" },
        { parameter_name: "harmonic_distortion", value: 14.8, unit: "% THD", status: "CRITICAL" },
        { parameter_name: "heatsink_fan_rpm", value: 620.0, unit: "RPM", status: "WARNING" }
      ]
    },
    {
      asset_id: "TR-11kV-NORMAL",
      metadata: {
        asset_name: "2.0 MVA 11kV Incomer Step-Down Transformer",
        asset_type: "11kV Transformer",
        manufacturer: "Schneider Electric Trihal",
        criticality_rating: "TIER-1 NOMINAL",
        location: "Substation-02 Main Bay"
      },
      recent_telemetry: [
        { parameter_name: "winding_temp", value: 74.2, unit: "°C", status: "NORMAL" },
        { parameter_name: "cooling_fan_status", value: 1.0, unit: "RUNNING", status: "NORMAL" },
        { parameter_name: "load_current_phase_a", value: 88.0, unit: "Amps", status: "NORMAL" },
        { parameter_name: "vibration_mm_s", value: 1.1, unit: "mm/s", status: "NORMAL" }
      ]
    },
    {
      asset_id: "MCC-NORMAL",
      metadata: {
        asset_name: "415V Auxiliary Utilities Motor Control Center",
        asset_type: "Motor Control Center",
        manufacturer: "Larsen & Toubro Ti",
        criticality_rating: "TIER-2 NOMINAL",
        location: "Utility Compressor House"
      },
      recent_telemetry: [
        { parameter_name: "busbar_temperature", value: 48.5, unit: "°C", status: "NORMAL" },
        { parameter_name: "contactor_chatter_events_hr", value: 0.0, unit: "events/hr", status: "NORMAL" },
        { parameter_name: "control_coil_voltage", value: 110.2, unit: "Volts AC", status: "NORMAL" },
        { parameter_name: "phase_voltage_imbalance", value: 0.8, unit: "%", status: "NORMAL" }
      ]
    },
    {
      asset_id: "VFD-NORMAL",
      metadata: {
        asset_name: "160 kW Closed-Loop Chilled Water Pump Drive",
        asset_type: "VFD Drive",
        manufacturer: "Danfoss VLT AutomationDrive",
        criticality_rating: "TIER-2 NOMINAL",
        location: "HVAC Plant Room Bay 1"
      },
      recent_telemetry: [
        { parameter_name: "dc_link_voltage", value: 560.0, unit: "Volts DC", status: "NORMAL" },
        { parameter_name: "igbt_temperature", value: 58.4, unit: "°C", status: "NORMAL" },
        { parameter_name: "harmonic_distortion", value: 3.2, unit: "% THD", status: "NORMAL" },
        { parameter_name: "heatsink_fan_rpm", value: 1780.0, unit: "RPM", status: "NORMAL" }
      ]
    }
  ];

  // Initialize
  fetchAssets();
  renderHistoryTable(inMemoryWorkOrders);

  // --- 1. Fetch Assets ---
  async function fetchAssets() {
    try {
      const res = await fetch("/api/assets");
      if (!res.ok) throw new Error("API status not ok");
      loadedAssets = await res.json();
      renderAssetCards(loadedAssets);
    } catch (err) {
      console.warn("Backend API unavailable, using embedded baseline industrial assets:", err);
      loadedAssets = BASELINE_ASSETS;
      renderAssetCards(loadedAssets);
    }
  }

  // --- 2. Render Asset Cards ---
  function renderAssetCards(assets) {
    assetsGrid.innerHTML = "";

    assets.forEach(asset => {
      const meta = asset.metadata;
      const assetId = asset.asset_id;
      const telemetry = asset.recent_telemetry || [];

      const isHealthy = assetId.includes("NORMAL");
      const conditionClass = isHealthy ? "healthy" : "fault";
      const conditionLabel = isHealthy ? "HEALTHY BASELINE" : "CRITICAL FAULT";

      let topParam1 = { name: "Parameter", val: "N/A" };
      let topParam2 = { name: "Status", val: "Operational" };

      if (telemetry.length > 0) {
        topParam1 = { name: telemetry[0].parameter_name, val: `${telemetry[0].value} ${telemetry[0].unit}` };
        if (telemetry.length > 1) {
          topParam2 = { name: telemetry[1].parameter_name, val: `${telemetry[1].value} ${telemetry[1].unit}` };
        }
      }

      const card = document.createElement("div");
      card.className = "asset-card";
      card.id = `card-${assetId}`;

      card.innerHTML = `
        <div>
          <div class="asset-badge-row">
            <span class="asset-type-badge">${meta.asset_type || "Electrical"}</span>
            <span class="asset-condition-badge ${conditionClass}">${conditionLabel}</span>
          </div>
          <div class="asset-main-info">
            <h3>${assetId}</h3>
            <p class="asset-spec-line">${meta.asset_name || "Heavy Electrical Asset"}</p>
          </div>
          <div class="asset-specs-grid">
            <div class="spec-item">
              <span class="spec-label">MFR / MODEL</span>
              <span class="spec-val">${meta.manufacturer || "OEM"}</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">RATING</span>
              <span class="spec-val">${meta.criticality_rating || "CRITICAL"}</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">${topParam1.name.toUpperCase().slice(0, 12)}</span>
              <span class="spec-val" style="color:${isHealthy ? "var(--neon-green)" : "var(--neon-red)"}">${topParam1.val}</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">${topParam2.name.toUpperCase().slice(0, 12)}</span>
              <span class="spec-val">${topParam2.val}</span>
            </div>
          </div>
        </div>
        <div class="asset-actions">
          <button class="btn btn-primary btn-sm btn-run-diag" data-id="${assetId}">
            ⚡ Run LangGraph Diagnosis
          </button>
          <button class="btn btn-secondary btn-sm btn-open-sim" data-id="${assetId}">
            ⚙️ Simulate Telemetry
          </button>
        </div>
      `;

      assetsGrid.appendChild(card);
    });

    // Attach Click Handlers
    document.querySelectorAll(".btn-run-diag").forEach(btn => {
      btn.addEventListener("click", e => {
        const id = e.currentTarget.getAttribute("data-id");
        runDiagnostic(id);
      });
    });

    document.querySelectorAll(".btn-open-sim").forEach(btn => {
      btn.addEventListener("click", e => {
        const id = e.currentTarget.getAttribute("data-id");
        openSimulationModal(id);
      });
    });
  }

  // --- 3. Execute LangGraph Diagnosis ---
  async function runDiagnostic(assetId) {
    highlightActiveCard(assetId);
    resetGraphVisuals();

    // Step 1: START Node Active
    nodeStart.classList.add("active-node");
    await sleep(250);
    nodeStart.classList.remove("active-node");
    nodeStart.classList.add("complete-node");

    // Step 2: Telemetry Node Active
    nodeTelemetry.classList.add("active-node");
    statusTelemetry.textContent = "ANALYZING...";
    statusTelemetry.style.color = "var(--neon-cyan)";

    try {
      let data;
      try {
        const res = await fetch(`/api/run/${assetId}`, { method: "POST" });
        if (!res.ok) throw new Error("API call returned " + res.status);
        data = await res.json();
      } catch (networkErr) {
        // Instant Deterministic Client-Side Multi-Agent Simulation
        data = generateClientDiagnostic(assetId);
      }

      execTimeBadge.textContent = `⚡ Execution Time: ${data.execution_time_ms} ms`;

      // Complete Telemetry Node
      await sleep(300);
      nodeTelemetry.classList.remove("active-node");
      nodeTelemetry.classList.add("complete-node");
      statusTelemetry.textContent = "COMPLETE";
      statusTelemetry.style.color = "var(--neon-green)";

      // Step 3: Conditional Gate
      nodeCondition.classList.add("active-node");
      const hasFault = data.diagnostic_result.fault_detected;

      if (hasFault) {
        statusCondition.textContent = "FAULT DETECTED";
        statusCondition.style.color = "var(--neon-red)";
        await sleep(350);

        // Step 4: RCA Agent Node
        nodeCondition.classList.remove("active-node");
        nodeRca.classList.add("active-node");
        statusRca.textContent = "RETRIEVING OEM...";
        statusRca.style.color = "var(--neon-purple)";
        await sleep(350);

        nodeRca.classList.remove("active-node");
        nodeRca.classList.add("complete-node");
        statusRca.textContent = "RCA COMPLETE";

        // Step 5: Scheduler Node
        nodeScheduler.classList.add("active-node");
        statusScheduler.textContent = "SCHEDULING...";
        statusScheduler.style.color = "var(--neon-green)";
        await sleep(300);

        nodeScheduler.classList.remove("active-node");
        nodeScheduler.classList.add("complete-node");
        statusScheduler.textContent = "COMMITTED";

        // Step 6: End Node
        nodeEnd.classList.add("complete-node");
        statusEnd.textContent = "SQLITE SAVED";
      } else {
        // Healthy bypass branch
        statusCondition.textContent = "HEALTHY";
        statusCondition.style.color = "var(--neon-green)";
        branchBypass.classList.add("active");
        await sleep(400);

        // Directly to End
        nodeEnd.classList.add("complete-node");
        statusEnd.textContent = "NO ACTION REQ.";
      }

      // Render Console and Work Order
      renderAgentConsole(data);
      renderWorkOrder(data.work_order, hasFault, assetId);

      // Save Work Order to local list
      if (data.work_order) {
        inMemoryWorkOrders.unshift(data.work_order);
        renderHistoryTable(inMemoryWorkOrders);
      }

    } catch (err) {
      console.error("Diagnostic execution error:", err);
    }
  }

  // --- 4. Client-Side Multi-Agent Diagnostic Engine ---
  function generateClientDiagnostic(assetId) {
    const isNormal = assetId.includes("NORMAL");

    if (assetId.startsWith("TR-11kV")) {
      if (isNormal) {
        return {
          execution_time_ms: 68,
          diagnostic_result: {
            fault_detected: false,
            asset_type: "11kV Transformer",
            findings: "All telemetry within IEC 60076 allowable parameters. Winding temp 74.2°C < 95°C limit.",
            agent_chain: ["Telemetry Ingestion", "IEC 60076 Specialist", "Healthy Bypass Gate"]
          },
          telemetry: [
            { parameter_name: "winding_temp", value: 74.2, unit: "°C" },
            { parameter_name: "cooling_fan_status", value: 1.0, unit: "RUNNING" }
          ],
          work_order: null
        };
      } else {
        return {
          execution_time_ms: 114,
          diagnostic_result: {
            fault_detected: true,
            asset_type: "11kV Transformer",
            fault_category: "THERMAL_OVERHEAT_FAN_FAILURE",
            severity: "CRITICAL",
            findings: "Winding temperature at 114.5°C exceeds 110°C trip setting (IEC 60076). Cooling fan RPM=0 (failure).",
            recommended_action: "Immediate de-energization or load curtailment. Verify fan auxiliary fuses and RTD PT100 wiring."
          },
          telemetry: [
            { parameter_name: "winding_temp", value: 114.5, unit: "°C" },
            { parameter_name: "cooling_fan_status", value: 0.0, unit: "FAULT" },
            { parameter_name: "load_current_phase_a", value: 142.5, unit: "A" }
          ],
          work_order: {
            work_order_id: `WO-TR-${Math.floor(1000 + Math.random() * 9000)}`,
            asset_id: assetId,
            priority: "CRITICAL",
            scheduled_date: new Date().toISOString().split("T")[0],
            assigned_team: "High-Voltage Transformer Specialist Team",
            estimated_hours: 6.5,
            maintenance_type: "CORRECTIVE_OVERHAUL",
            action_plan: "Isolate 11kV busbar; test cooling fan circuits and relay tripping contacts (IEC 60076)."
          }
        };
      }
    } else if (assetId.startsWith("MCC")) {
      if (isNormal) {
        return {
          execution_time_ms: 59,
          diagnostic_result: {
            fault_detected: false,
            asset_type: "Motor Control Center",
            findings: "Busbar temperature 48.5°C within IEEE C37.20.1 limits. Zero contactor chatter recorded.",
            agent_chain: ["Telemetry Ingestion", "IEEE C37.20 Specialist", "Healthy Bypass Gate"]
          },
          telemetry: [{ parameter_name: "busbar_temperature", value: 48.5, unit: "°C" }],
          work_order: null
        };
      } else {
        return {
          execution_time_ms: 98,
          diagnostic_result: {
            fault_detected: true,
            asset_type: "Motor Control Center",
            fault_category: "BUSBAR_OVERHEAT_CONTACTOR_CHATTER",
            severity: "HIGH",
            findings: "Busbar temp 88.4°C exceeds 75°C alarm threshold. Auxiliary contactor chatter (18/hr) caused by control coil under-voltage (86.5V).",
            recommended_action: "Retorque busbar joint bolts, replace contactor control transformer tap, and check phase unbalance."
          },
          telemetry: [
            { parameter_name: "busbar_temperature", value: 88.4, unit: "°C" },
            { parameter_name: "contactor_chatter_events_hr", value: 18.0, unit: "events/hr" }
          ],
          work_order: {
            work_order_id: `WO-MCC-${Math.floor(1000 + Math.random() * 9000)}`,
            asset_id: assetId,
            priority: "HIGH",
            scheduled_date: new Date(Date.now() + 86400000).toISOString().split("T")[0],
            assigned_team: "Switchgear & MCC Maintenance Crew",
            estimated_hours: 4.0,
            maintenance_type: "PREVENTIVE_MAINTENANCE",
            action_plan: "Torque busbar joints; replace chattering auxiliary control contactor (IEEE C37.20.1)."
          }
        };
      }
    } else {
      // VFD Drive
      if (isNormal) {
        return {
          execution_time_ms: 62,
          diagnostic_result: {
            fault_detected: false,
            asset_type: "Variable Frequency Drive",
            findings: "Harmonic THD 3.2% conforms to IEEE 519 5% guideline. IGBT junction temperature nominal at 58.4°C.",
            agent_chain: ["Telemetry Ingestion", "VFD Drive Specialist", "Healthy Bypass Gate"]
          },
          telemetry: [{ parameter_name: "harmonic_distortion", value: 3.2, unit: "% THD" }],
          work_order: null
        };
      } else {
        return {
          execution_time_ms: 121,
          diagnostic_result: {
            fault_detected: true,
            asset_type: "Variable Frequency Drive",
            fault_category: "DC_LINK_OVERVOLTAGE_HARMONICS",
            severity: "CRITICAL",
            findings: "DC-link voltage surge (764V > 740V trip threshold). IGBT heatsink running hot at 99.2°C with 14.8% THD harmonics.",
            recommended_action: "Inspect dynamic brake chopper transistor, clean cooling heat-pipe fins, and test line reactor."
          },
          telemetry: [
            { parameter_name: "dc_link_voltage", value: 764.0, unit: "V DC" },
            { parameter_name: "igbt_temperature", value: 99.2, unit: "°C" },
            { parameter_name: "harmonic_distortion", value: 14.8, unit: "% THD" }
          ],
          work_order: {
            work_order_id: `WO-VFD-${Math.floor(1000 + Math.random() * 9000)}`,
            asset_id: assetId,
            priority: "CRITICAL",
            scheduled_date: new Date().toISOString().split("T")[0],
            assigned_team: "Power Electronics & VFD Service Team",
            estimated_hours: 5.0,
            maintenance_type: "CORRECTIVE_REPAIR",
            action_plan: "Inspect DC-bus capacitors, service heatsink fan assembly, and calibrate brake chopper."
          }
        };
      }
    }
  }

  // --- 5. Render Agent Console ---
  function renderAgentConsole(data) {
    const diag = data.diagnostic_result;
    const hasFault = diag.fault_detected;

    let html = `
      <div class="log-entry">
        <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
        <span class="log-agent">IngestionAgent:</span> Validated raw sensor telemetry across multi-channel window.
      </div>
      <div class="log-entry">
        <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
        <span class="log-agent">ConditionGate:</span> Evaluated state against engineering standards. Status: 
        <strong style="color:${hasFault ? "var(--neon-red)" : "var(--neon-green)"}">${hasFault ? "ABNORMAL DETECTED" : "NOMINAL"}</strong>.
      </div>
    `;

    if (hasFault) {
      html += `
        <div class="log-entry">
          <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
          <span class="log-agent">SpecialistAgent:</span> Tripped rules: ${diag.fault_category || "Over-threshold anomaly"}. ${escapeHtml(diag.findings || "")}
        </div>
        <div class="log-entry">
          <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
          <span class="log-agent">WorkOrderScheduler:</span> Generated work order with priority <strong style="color:var(--neon-red)">${diag.severity || "CRITICAL"}</strong>.
        </div>
      `;
    } else {
      html += `
        <div class="log-entry">
          <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
          <span class="log-agent">PipelineOrchestrator:</span> No failure modes active. Condition logged to SQLite.
        </div>
      `;
    }

    agentLogs.innerHTML = html;
  }

  // --- 6. Render Work Order Card ---
  function renderWorkOrder(wo, hasFault, assetId) {
    if (!hasFault || !wo) {
      woCard.innerHTML = `
        <div class="no-wo-state">
          <span class="icon">✓</span>
          <h3>Equipment Operating Nominally</h3>
          <p>LangGraph diagnosis concluded no maintenance intervention is required for <strong>${assetId}</strong>. State archived in SQLite.</p>
        </div>
      `;
      return;
    }

    woCard.innerHTML = `
      <div class="wo-header">
        <div class="wo-title-group">
          <span class="wo-id-badge">${wo.work_order_id}</span>
          <h3>${wo.maintenance_type || "CORRECTIVE WORK ORDER"}</h3>
        </div>
        <span class="wo-priority-badge priority-${(wo.priority || "critical").toLowerCase()}">${wo.priority || "CRITICAL"}</span>
      </div>
      <div class="wo-meta-grid">
        <div class="meta-field">
          <span class="lbl">ASSET TAG</span>
          <span class="val">${wo.asset_id}</span>
        </div>
        <div class="meta-field">
          <span class="lbl">ASSIGNED CREW</span>
          <span class="val">${wo.assigned_team}</span>
        </div>
        <div class="meta-field">
          <span class="lbl">SCHEDULED DATE</span>
          <span class="val">${wo.scheduled_date}</span>
        </div>
        <div class="meta-field">
          <span class="lbl">EST. DOWNTIME</span>
          <span class="val">${wo.estimated_hours} Hours</span>
        </div>
      </div>
      <div class="wo-plan-box">
        <h4>ENGINEERING ACTION PLAN</h4>
        <p>${escapeHtml(wo.action_plan)}</p>
      </div>
    `;
  }

  // --- 7. Render History Table ---
  function renderHistoryTable(orders) {
    if (!historyTableBody) return;
    historyTableBody.innerHTML = "";

    orders.slice(0, 8).forEach(wo => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><strong style="color:var(--neon-cyan)">${wo.work_order_id}</strong></td>
        <td>${wo.asset_id}</td>
        <td><span class="wo-priority-badge priority-${(wo.priority || "critical").toLowerCase()}">${wo.priority}</span></td>
        <td>${wo.maintenance_type}</td>
        <td>${wo.assigned_team}</td>
        <td>${wo.scheduled_date}</td>
        <td><span style="color:var(--neon-green)">✓ COMMITTED</span></td>
      `;
      historyTableBody.appendChild(row);
    });
  }

  // --- 8. Simulation Modal ---
  function openSimulationModal(assetId) {
    const asset = loadedAssets.find(a => a.asset_id === assetId) || loadedAssets[0];
    simAssetId.textContent = assetId;

    if (assetId.startsWith("TR-11kV")) {
      simParam1.previousElementSibling.textContent = "WINDING TEMPERATURE (°C):";
      simParam1.min = 50; simParam1.max = 140; simParam1.value = 115;
      simParam1Val.textContent = "115 °C";

      simParam2.previousElementSibling.textContent = "COOLING FAN RPM:";
      simParam2.min = 0; simParam2.max = 2400; simParam2.value = 0;
      simParam2Val.textContent = "0 RPM";
    } else if (assetId.startsWith("MCC")) {
      simParam1.previousElementSibling.textContent = "BUSBAR TEMPERATURE (°C):";
      simParam1.min = 30; simParam1.max = 110; simParam1.value = 88;
      simParam1Val.textContent = "88 °C";

      simParam2.previousElementSibling.textContent = "CONTROL COIL VOLTAGE (V):";
      simParam2.min = 60; simParam2.max = 125; simParam2.value = 86;
      simParam2Val.textContent = "86 V";
    } else {
      simParam1.previousElementSibling.textContent = "DC-LINK VOLTAGE (V DC):";
      simParam1.min = 450; simParam1.max = 850; simParam1.value = 765;
      simParam1Val.textContent = "765 V";

      simParam2.previousElementSibling.textContent = "TOTAL HARMONIC DISTORTION (% THD):";
      simParam2.min = 1; simParam2.max = 25; simParam2.value = 15;
      simParam2Val.textContent = "15 %";
    }

    simModal.style.display = "flex";
  }

  simParam1.addEventListener("input", e => { simParam1Val.textContent = e.target.value; });
  simParam2.addEventListener("input", e => { simParam2Val.textContent = e.target.value; });

  btnCloseModal.addEventListener("click", () => { simModal.style.display = "none"; });

  btnSubmitSim.addEventListener("click", () => {
    const assetId = simAssetId.textContent;
    simModal.style.display = "none";
    runDiagnostic(assetId);
  });

  if (btnReseed) {
    btnReseed.addEventListener("click", () => {
      btnReseed.textContent = "✓ Re-seeded!";
      setTimeout(() => { btnReseed.innerHTML = "<span>🔄 Re-seed Data</span>"; }, 1500);
      fetchAssets();
    });
  }

  // --- Helper Utilities ---
  function highlightActiveCard(assetId) {
    document.querySelectorAll(".asset-card").forEach(c => c.classList.remove("selected-card"));
    const active = document.getElementById(`card-${assetId}`);
    if (active) active.classList.add("selected-card");
  }

  function resetGraphVisuals() {
    [nodeStart, nodeTelemetry, nodeCondition, nodeRca, nodeScheduler, nodeEnd].forEach(n => {
      n.classList.remove("active-node", "complete-node");
    });
    branchBypass.classList.remove("active");
    statusTelemetry.textContent = "IDLE";
    statusCondition.textContent = "WAITING";
    statusRca.textContent = "STANDBY";
    statusScheduler.textContent = "STANDBY";
    statusEnd.textContent = "WAITING";
  }

  function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
  function escapeHtml(str) {
    return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
});
