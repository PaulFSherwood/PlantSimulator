(function () {
  const stateUrl = "/api/state";
  let lastState = null;

  function getPath(obj, path) {
    return path.split(".").reduce((cur, key) => (cur == null ? undefined : cur[key]), obj);
  }

  function formatValue(value, format) {
    if (value == null) return "--";
    if (format === "currency") return "$" + Math.round(Number(value)).toLocaleString();
    if (format === "percent") return Number(value).toFixed(Number(value) % 1 === 0 ? 0 : 1) + "%";
    if (format === "tons") return Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 }) + " ton";
    if (format === "rate-ton") return Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 }) + " ton/hr";
    if (format === "rate-bu") return Math.round(Number(value)).toLocaleString() + " bu/hr";
    if (format === "bags-hour") return Math.round(Number(value)).toLocaleString() + " bag/hr";
    if (format === "temp-f") return Number(value).toFixed(1) + "°F";
    if (format === "running-label") return value ? "Live" : "Paused";
    if (format === "status") return String(value).replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
    if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    if (typeof value === "boolean") return value ? "On" : "Off";
    return String(value);
  }

  function statusDotClass(status) {
    if (["running"].includes(status)) return "good-dot";
    if (["warning", "stopped"].includes(status)) return "warn-dot";
    return "bad-dot";
  }

  function healthClass(health) {
    return health >= 85 ? "good-health" : "warn-health";
  }

  function escapeHtml(text) {
    return String(text ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function updateLiveText(state) {
    document.querySelectorAll("[data-live]").forEach((el) => {
      const value = getPath(state, el.dataset.live);
      el.textContent = formatValue(value, el.dataset.format || "");
    });

    document.querySelectorAll("[data-live-count]").forEach((el) => {
      const value = getPath(state, el.dataset.liveCount);
      el.textContent = Array.isArray(value) ? value.length : value ? Object.keys(value).length : 0;
    });

    document.querySelectorAll("[data-live-style]").forEach((el) => {
      const value = getPath(state, el.dataset.liveStyle);
      const prop = el.dataset.styleProp || "--value";
      const formatted = el.dataset.styleFormat === "percent" ? `${Number(value || 0)}%` : String(value ?? "");
      el.style.setProperty(prop, formatted);
    });

    const dock = document.querySelector("[data-sim-dock]");
    if (dock) dock.classList.toggle("is-paused", !state.sim.running);
  }

  function equipmentRows(equipment) {
    return Object.values(equipment).map(eq => `
      <tr>
        <td>${escapeHtml(eq.name)}</td>
        <td>${escapeHtml(eq.kind)}</td>
        <td><span class="dot ${statusDotClass(eq.status)}"></span>${formatValue(eq.status, "status")}${eq.locked_out ? " / Locked" : ""}</td>
        <td>${Number(eq.runtime_hours).toFixed(2)} h</td>
        <td><span class="health ${healthClass(eq.health)}" style="--health: ${eq.health}%;"></span></td>
        <td>${formatValue(eq.load_percent, "percent")}</td>
        <td>${formatValue(eq.temperature_f, "temp-f")}</td>
        <td class="row-actions">
          <button type="button" data-equipment-action="start" data-equipment-id="${eq.id}">Start</button>
          <button type="button" data-equipment-action="stop" data-equipment-id="${eq.id}">Stop</button>
          ${eq.locked_out
            ? `<button type="button" data-equipment-action="clear_lockout" data-equipment-id="${eq.id}">Clear LOTO</button>`
            : `<button type="button" data-equipment-action="lockout" data-equipment-id="${eq.id}">Lockout</button>`}
        </td>
      </tr>
    `).join("");
  }

  function equipmentSummaryRows(equipment) {
    return Object.values(equipment).slice(0, 6).map(eq => `
      <tr>
        <td>${escapeHtml(eq.name)}</td>
        <td><span class="dot ${statusDotClass(eq.status)}"></span>${formatValue(eq.status, "status")}</td>
        <td>${Number(eq.runtime_hours).toFixed(2)} h</td>
        <td><span class="health ${healthClass(eq.health)}" style="--health: ${eq.health}%;"></span></td>
      </tr>
    `).join("");
  }

  function alarmRail(alarms) {
    return alarms.slice(0, 4).map(alarm => `
      <div class="rail-alarm ${escapeHtml(alarm.severity)} ${alarm.acknowledged ? "is-ack" : ""}">
        <div><strong>${escapeHtml(alarm.title)}</strong><span>${escapeHtml(alarm.message)}</span></div>
        <div class="alarm-meta"><span>${escapeHtml(alarm.age)}</span><em>${escapeHtml(alarm.severity)}</em></div>
      </div>
    `).join("");
  }

  function alarmsPage(alarms) {
    return alarms.map(alarm => `
      <div class="alarm-card ${escapeHtml(alarm.severity)} ${alarm.acknowledged ? "is-ack" : ""}">
        <div><strong>${escapeHtml(alarm.title)}</strong><span>${escapeHtml(alarm.equipment)} — ${escapeHtml(alarm.message)}</span></div>
        <div class="alarm-meta"><span>${escapeHtml(alarm.age)}</span><em>${escapeHtml(alarm.severity)}</em>${alarm.acknowledged ? "<b>Ack</b>" : `<button type="button" data-alarm-ack="${alarm.id}">Ack</button>`}</div>
      </div>
    `).join("");
  }

  function equipmentListItems(state, ids) {
    return ids.map(id => state.equipment[id]).filter(Boolean).map(eq => `
      <li><span>${escapeHtml(eq.name)}</span><strong class="${eq.status === "running" ? "good-text" : "warning-text"}">${formatValue(eq.status, "status")}</strong></li>
    `).join("");
  }

  function materialFlow(state) {
    const flow = state.process.flow;
    return [
      ["Receiving → Wet Bin", flow.receiving_to_wet],
      ["Wet Bin → Dryer", flow.wet_to_dryer],
      ["Dryer → Dry Bin", flow.dryer_to_dry],
      ["Dry Bin → Packaging", flow.dry_to_packaging],
    ].map(([label, value]) => `<div><span>${label}</span><strong>${formatValue(value, "rate-ton")}</strong></div>`).join("");
  }

  function workOrders(state) {
    return state.maintenance.work_orders.map(wo => `<tr><td>${wo.id}</td><td>${wo.equipment}</td><td>${wo.priority}</td><td>${wo.status}</td><td>${wo.task}</td></tr>`).join("");
  }

  function lotoRecords(state) {
    return state.loto.records.map(r => `<tr><td>${r.id}</td><td>${r.equipment}</td><td>${r.owner}</td><td>${r.status}</td><td>${r.reason}</td><td><button type="button" data-equipment-action="clear_lockout" data-equipment-id="${r.equipment_id}">Clear</button></td></tr>`).join("");
  }

  function eventLog(state) {
    return state.history.events.slice(0, 12).map(ev => `<div><span>${escapeHtml(ev.time)}</span><strong>${escapeHtml(ev.message)}</strong></div>`).join("");
  }

  function ioList(items) {
    return items.map(item => `<div><span>${escapeHtml(item.tag)}</span><strong>${formatValue(item.value, "")}</strong><em>${escapeHtml(item.label)}</em></div>`).join("");
  }

  function faultButtons(state) {
    return Object.values(state.equipment).map(eq => `<button type="button" data-inject-fault="${eq.id}" data-severity="high"><strong>${escapeHtml(eq.name)}</strong><span>Inject fault</span></button>`).join("");
  }

  function renderChart(el, state) {
    const samples = state.history.production || [];
    if (!samples.length) {
      el.innerHTML = `<div class="chart-empty">Waiting for production samples...</div>`;
      return;
    }
    const max = Math.max(...samples.map(s => s.rate), 1);
    el.innerHTML = samples.map(s => {
      const h = Math.max(4, (s.rate / max) * 100);
      return `<span title="${s.time}: ${formatValue(s.rate, "rate-ton")}" style="height:${h}%"></span>`;
    }).join("");
  }

  function updateLists(state) {
    const renderers = {
      "equipment-summary": () => equipmentSummaryRows(state.equipment),
      "equipment-full": () => equipmentRows(state.equipment),
      "alarm-rail": () => alarmRail(state.alarms),
      "alarms-page": () => alarmsPage(state.alarms),
      "receiving-equipment": () => equipmentListItems(state, ["receiving_hopper", "wet_bin_auger", "elevator_1"]),
      "dryer-equipment": () => equipmentListItems(state, ["dryer_line_1", "wet_bin_auger"]),
      "milling-equipment": () => equipmentListItems(state, ["mixer_1", "conveyor_2"]),
      "packaging-equipment": () => equipmentListItems(state, ["packaging_line_1", "dry_bin"]),
      "material-flow": () => materialFlow(state),
      "work-orders": () => workOrders(state),
      "loto-records": () => lotoRecords(state),
      "event-log": () => eventLog(state),
      "io-inputs": () => ioList(state.io.inputs),
      "io-outputs": () => ioList(state.io.outputs),
      "fault-buttons": () => faultButtons(state),
    };

    document.querySelectorAll("[data-live-list]").forEach(el => {
      const renderer = renderers[el.dataset.liveList];
      if (renderer) el.innerHTML = renderer();
    });

    document.querySelectorAll("[data-live-chart='production']").forEach(el => renderChart(el, state));
  }

  async function fetchState() {
    const response = await fetch(stateUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(`State fetch failed: ${response.status}`);
    lastState = await response.json();
    updateLiveText(lastState);
    updateLists(lastState);
  }

  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) throw new Error(`POST failed: ${response.status}`);
    lastState = await response.json();
    updateLiveText(lastState);
    updateLists(lastState);
  }

  document.addEventListener("click", (event) => {
    const simButton = event.target.closest("[data-sim-action]");
    if (simButton) {
      const action = simButton.dataset.simAction;
      postJson(`/api/sim/${action}`).catch(console.error);
      return;
    }

    const eqButton = event.target.closest("[data-equipment-action]");
    if (eqButton) {
      const id = eqButton.dataset.equipmentId;
      const action = eqButton.dataset.equipmentAction;
      postJson(`/api/equipment/${id}/${action}`, { reason: "UI command" }).catch(console.error);
      return;
    }

    const alarmButton = event.target.closest("[data-alarm-ack]");
    if (alarmButton) {
      postJson(`/api/alarms/${alarmButton.dataset.alarmAck}/ack`).catch(console.error);
      return;
    }

    const faultButton = event.target.closest("[data-inject-fault]");
    if (faultButton) {
      postJson("/api/faults/inject", { equipment_id: faultButton.dataset.injectFault, severity: faultButton.dataset.severity || "high" }).catch(console.error);
      return;
    }

    const totpButton = event.target.closest("[data-totp-setup]");
    if (totpButton) {
      fetch("/api/auth/totp/setup", { method: "POST" })
        .then(r => r.json())
        .then(data => {
          const out = document.querySelector("[data-totp-output]");
          if (!out) return;
          if (data.error) {
            out.innerHTML = `<div class="form-error">${escapeHtml(data.error)}</div>`;
          } else {
            out.innerHTML = `<div class="code-card"><strong>Secret:</strong> ${escapeHtml(data.secret)}<br><strong>URI:</strong> ${escapeHtml(data.uri)}</div>`;
          }
        })
        .catch(console.error);
      return;
    }

    const reportButton = event.target.closest("[data-report-refresh]");
    if (reportButton) {
      fetch("/api/reports/daily", { cache: "no-store" })
        .then(r => r.json())
        .then(data => { reportButton.textContent = `Report refreshed (${data.sample_count} samples)`; })
        .catch(console.error);
    }
  });

  fetchState().catch(console.error);
  setInterval(() => fetchState().catch(console.error), 2000);
})();
