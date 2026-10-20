/**
 * app.js - Client Controller for Multi-Agent Predictive Maintenance Dashboard.
 * Coordinates 1-click diagnostics, LangGraph node animations, live simulation,
 * and SQLite audit logging.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const assetsGrid = document.getElementById("assets-grid");
  const consoleLogs = document.getElementById("console-logs");
  const workorderDisplay = document.getElementById("workorder-display");
  const historyTableBody = document.getElementById("history-table-body");
  const execTimeBadge = document.getElementById("execution-time-badge");
  const btnRunAll = document.getElementById("btn-run-all");
  const btnReseed = document.getElementById("btn-reseed");
  const btnRefreshHistory = document.getElementById("btn-refresh-history");
  const btnCopyWo = document.getElementById("btn-copy-wo");
  const btnPrintWo = document.getElementById("btn-print-wo");
  const btnTriggerSim = document.getElementById("btn-trigger-sim");

  // Slider inputs
  const inputWinding = document.getElementById("input-winding-temp");
  const valWinding = document.getElementById("val-winding-temp");
  const inputDc = document.getElementById("input-dc-volts");
  const valDc = document.getElementById("val-dc-volts");
  const inputBusbar = document.getElementById("input-busbar-temp");
  const valBusbar = document.getElementById("val-busbar-temp");
  const inputThd = document.getElementById("input-thd");
  const valThd = document.getElementById("val-thd");

  // LangGraph Nodes
  const nodeStart = document.getElementById("node-start");
  const nodeTelemetry = document.getElementById("node-telemetry");
  const statusTelemetry = document.getElementById("status-telemetry");
  const nodeCondition = document.getElementById("node-condition");
  const statusCondition = document.getElementById("status-condition");
  const branchBypass = document.getElementById("branch-bypass");
  const nodeRca = document.getElementById("node-rca");
  const statusRca = document.getElementById("status-rca");
  const nodeScheduler = document.getElementById("node-scheduler");
  const statusScheduler = document.getElementById("status-scheduler");
  const nodeEnd = document.getElementById("node-end");
  const statusEnd = document.getElementById("status-end");

  let currentWorkOrderMarkdown = "";
  let loadedAssets = [];

  // -------------------------------------------------------------
  // 1. Initial Load: Fetch Assets & History
  // -------------------------------------------------------------
  fetchAssets();
  fetchWorkOrderHistory();

  // Slider updates
  inputWinding.addEventListener("input", (e) => valWinding.textContent = `${e.target.value} °C`);
  inputDc.addEventListener("input", (e) => valDc.textContent = `${e.target.value} V`);
  inputBusbar.addEventListener("input", (e) => valBusbar.textContent = `${e.target.value} °C`);
  inputThd.addEventListener("input", (e) => valThd.textContent = `${e.target.value} %`);

  // -------------------------------------------------------------
  // 2. Fetch Assets & Render Cards
  // -------------------------------------------------------------
  async function fetchAssets() {
    try {
      const res = await fetch("/api/assets");
      loadedAssets = await res.json();
      renderAssetCards(loadedAssets);
    } catch (err) {
      console.error("Failed to load assets:", err);
      assetsGrid.innerHTML = `<div class="asset-card">Error loading assets from backend server.</div>`;
    }
  }

  function renderAssetCards(assets) {
    assetsGrid.innerHTML = "";

    assets.forEach(asset => {
      const meta = asset.metadata;
      const assetId = asset.asset_id;
      const telemetry = asset.recent_telemetry || [];

      // Determine condition preview
      const isHealthy = assetId.includes("NORMAL");
      const conditionClass = isHealthy ? "healthy" : "fault";
      const conditionLabel = isHealthy ? "HEALTHY BASELINE" : "CRITICAL FAULT";

      // Pick top 2 telemetry values
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
          <div class="telemetry-mini-strip">
            <div class="mini-stat">
              <div class="stat-label">${topParam1.name.replace(/_/g, ' ')}</div>
              <div class="stat-val ${!isHealthy ? 'alarm' : ''}">${topParam1.val}</div>
            </div>
            <div class="mini-stat">
              <div class="stat-label">${topParam2.name.replace(/_/g, ' ')}</div>
              <div class="stat-val">${topParam2.val}</div>
            </div>
          </div>
        </div>
        <button class="btn btn-primary asset-card-btn" data-asset="${assetId}">
          ⚡ 1-Click Diagnose (${assetId})
        </button>
      `;

      card.querySelector(".asset-card-btn").addEventListener("click", () => {
        runDiagnostic(assetId);
      });

      assetsGrid.appendChild(card);
    });
  }

  // -------------------------------------------------------------
  // 3. LangGraph Workflow Execution & Animation
  // -------------------------------------------------------------
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

    // Call API
    try {
      const res = await fetch(`/api/run/${assetId}`, { method: "POST" });
      const data = await res.json();

      execTimeBadge.textContent = `⚡ Execution Time: ${data.execution_time_ms} ms`;

      // Complete Telemetry Node
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

      // Refresh SQLite History table
      fetchWorkOrderHistory();

    } catch (err) {
      console.error("Diagnostic execution error:", err);
      nodeTelemetry.classList.remove("active-node");
      statusTelemetry.textContent = "ERROR";
      statusTelemetry.style.color = "var(--neon-red)";
    }
  }

  // -------------------------------------------------------------
  // 4. Custom Parameter Simulation
  // -------------------------------------------------------------
  btnTriggerSim.addEventListener("click", async () => {
    resetGraphVisuals();

    const customParams = {
      "winding_temp": parseFloat(inputWinding.value),
      "dc_link_voltage": parseFloat(inputDc.value),
      "busbar_temperature": parseFloat(inputBusbar.value),
      "harmonic_distortion": parseFloat(inputThd.value)
    };

    // Determine target based on most extreme slider
    let targetAsset = "TR-11kV-01";
    if (customParams["dc_link_voltage"] > 700) {
      targetAsset = "VFD-04";
    } else if (customParams["busbar_temperature"] > 75) {
      targetAsset = "MCC-02";
    }

    highlightActiveCard(targetAsset);

    // Animate Telemetry
    nodeStart.classList.add("complete-node");
    nodeTelemetry.classList.add("active-node");
    statusTelemetry.textContent = "SIMULATING...";

    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_id: targetAsset,
          custom_parameters: customParams
        })
      });
      const data = await res.json();

      execTimeBadge.textContent = `⚡ Simulated in: ${data.execution_time_ms} ms`;
      nodeTelemetry.classList.remove("active-node");
      nodeTelemetry.classList.add("complete-node");
      statusTelemetry.textContent = "COMPLETE";

      const hasFault = data.diagnostic_result.fault_detected;
      if (hasFault) {
        nodeCondition.classList.add("complete-node");
        statusCondition.textContent = "FAULT DETECTED";
        nodeRca.classList.add("complete-node");
        statusRca.textContent = "RCA COMPLETE";
        nodeScheduler.classList.add("complete-node");
        statusScheduler.textContent = "COMMITTED";
        nodeEnd.classList.add("complete-node");
        statusEnd.textContent = "SQLITE SAVED";
      } else {
        branchBypass.classList.add("active");
        nodeEnd.classList.add("complete-node");
        statusEnd.textContent = "NO ACTION REQ.";
      }

      renderAgentConsole(data);
      renderWorkOrder(data.work_order, hasFault, targetAsset);
      fetchWorkOrderHistory();

    } catch (err) {
      console.error("Simulation error:", err);
    }
  });

  // -------------------------------------------------------------
  // 5. Batch Run All Assets Sequentially
  // -------------------------------------------------------------
  btnRunAll.addEventListener("click", async () => {
    btnRunAll.disabled = true;
    btnRunAll.textContent = "⏳ Running Batch Diagnostic...";

    for (const asset of loadedAssets) {
      await runDiagnostic(asset.asset_id);
      await sleep(1000);
    }

    btnRunAll.disabled = false;
    btnRunAll.textContent = "⚡ Run Diagnostic On All Assets (Batch)";
  });

  // -------------------------------------------------------------
  // 6. Reseed Database
  // -------------------------------------------------------------
  btnReseed.addEventListener("click", async () => {
    if (confirm("Reset SQLite database with fresh initial telemetry and OEM manual chunks?")) {
      btnReseed.disabled = true;
      btnReseed.textContent = "⏳ Resetting...";
      try {
        const res = await fetch("/api/reseed", { method: "POST" });
        const data = await res.json();
        alert(data.message);
        fetchAssets();
        fetchWorkOrderHistory();
      } finally {
        btnReseed.disabled = false;
        btnReseed.textContent = "🔄 Re-seed Data";
      }
    }
  });

  // -------------------------------------------------------------
  // 7. Render Console Logs
  // -------------------------------------------------------------
  function renderAgentConsole(data) {
    consoleLogs.innerHTML = "";
    const messages = data.messages || [];

    if (messages.length === 0) {
      consoleLogs.innerHTML = `<div class="empty-state">No agent thoughts recorded.</div>`;
      return;
    }

    messages.forEach((msg, idx) => {
      const block = document.createElement("div");
      let agentClass = "agent-telemetry";
      let agentTitle = "NODE 1: Telemetry Diagnostics Agent";

      if (msg.role.includes("manual") || msg.role.includes("rca")) {
        agentClass = "agent-rca";
        agentTitle = "NODE 2: Manual Retrieval & RCA Agent";
      } else if (msg.role.includes("scheduler") || msg.role.includes("work_order")) {
        agentClass = "agent-scheduler";
        agentTitle = "NODE 3: Work Order & Maintenance Scheduler Agent";
      }

      block.className = `agent-message-block ${agentClass}`;
      block.innerHTML = `
        <div class="agent-message-header">
          <span>${agentTitle}</span>
          <span>STEP #${idx + 1}</span>
        </div>
        <div class="agent-message-content">${escapeHtml(msg.content)}</div>
      `;
      consoleLogs.appendChild(block);
    });

    consoleLogs.scrollTop = consoleLogs.scrollHeight;
  }

  // -------------------------------------------------------------
  // 8. Render Work Order Output
  // -------------------------------------------------------------
  function renderWorkOrder(workOrderMd, hasFault, assetId) {
    currentWorkOrderMarkdown = workOrderMd;

    if (!hasFault || !workOrderMd) {
      workorderDisplay.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon" style="color: var(--neon-green)">✅</div>
          <h4 style="color: var(--neon-green)">Equipment Fully Operational</h4>
          <p>Asset <strong>${assetId}</strong> telemetry readings are within nominal tolerances. The conditional edge routed directly to END. No Work Order required.</p>
        </div>
      `;
      return;
    }

    workorderDisplay.innerHTML = `
      <div class="workorder-markdown">${escapeHtml(workOrderMd)}</div>
    `;
    workorderDisplay.scrollTop = 0;
  }

  // -------------------------------------------------------------
  // 9. Fetch & Render Work Order History Table
  // -------------------------------------------------------------
  async function fetchWorkOrderHistory() {
    try {
      const res = await fetch("/api/work_orders");
      const orders = await res.json();
      renderHistoryTable(orders);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  }

  btnRefreshHistory.addEventListener("click", fetchWorkOrderHistory);

  function renderHistoryTable(orders) {
    if (!orders || orders.length === 0) {
      historyTableBody.innerHTML = `<tr><td colspan="5" class="text-center" style="color: var(--text-dim); padding: 24px;">No work orders saved in SQLite yet.</td></tr>`;
      return;
    }

    historyTableBody.innerHTML = orders.map(o => `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: 600; color: var(--neon-cyan);">${o.order_id}</td>
        <td><strong>${o.asset_id}</strong></td>
        <td><span class="priority-pill ${o.priority}">${o.priority}</span></td>
        <td style="font-size: 0.78rem; color: var(--text-muted);">${o.scheduled_date}</td>
        <td><span class="status-tag">● ${o.status}</span></td>
      </tr>
    `).join("");
  }

  // -------------------------------------------------------------
  // 10. Copy & Print Handlers
  // -------------------------------------------------------------
  btnCopyWo.addEventListener("click", () => {
    if (!currentWorkOrderMarkdown) {
      alert("No active Work Order to copy.");
      return;
    }
    navigator.clipboard.writeText(currentWorkOrderMarkdown).then(() => {
      const originalText = btnCopyWo.textContent;
      btnCopyWo.textContent = "✅ Copied!";
      setTimeout(() => btnCopyWo.textContent = originalText, 1800);
    });
  });

  btnPrintWo.addEventListener("click", () => {
    if (!currentWorkOrderMarkdown) {
      alert("No active Work Order to print.");
      return;
    }
    const printWindow = window.open("", "_blank");
    printWindow.document.write(`
      <html>
        <head>
          <title>Formal Electrical Work Order</title>
          <style>
            body { font-family: monospace; padding: 20px; white-space: pre-wrap; font-size: 12px; }
          </style>
        </head>
        <body>${escapeHtml(currentWorkOrderMarkdown)}</body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  });

  // Helpers
  function highlightActiveCard(assetId) {
    document.querySelectorAll(".asset-card").forEach(c => c.classList.remove("active-selected"));
    const target = document.getElementById(`card-${assetId}`);
    if (target) target.classList.add("active-selected");
  }

  function resetGraphVisuals() {
    [nodeStart, nodeTelemetry, nodeCondition, nodeRca, nodeScheduler, nodeEnd].forEach(n => {
      n.classList.remove("active-node", "complete-node");
    });
    branchBypass.classList.remove("active");
    statusTelemetry.textContent = "IDLE";
    statusTelemetry.style.color = "var(--text-dim)";
    statusCondition.textContent = "GATE";
    statusCondition.style.color = "var(--text-dim)";
    statusRca.textContent = "IDLE";
    statusRca.style.color = "var(--text-dim)";
    statusScheduler.textContent = "IDLE";
    statusScheduler.style.color = "var(--text-dim)";
    statusEnd.textContent = "IDLE";
    statusEnd.style.color = "var(--text-dim)";
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
