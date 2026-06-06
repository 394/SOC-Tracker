const ALERT_STORAGE_KEY = "soc-alerts-v1";
const INTEGRATION_STORAGE_KEY = "soc-n8n-config-v1";
const THEME_STORAGE_KEY = "soc-theme-v1";
const API_BASE = "";
const STATUSES = ["New", "Triage", "Investigating", "Contained", "Closed"];
const SEVERITIES = ["Critical", "High", "Medium", "Low"];

const seedAlerts = [
  {
    id: "SOC-000001",
    title: "Impossible travel sign-in for finance admin",
    description: "Azure AD reported successful sign-ins from two countries within 11 minutes.",
    source: "Azure AD",
    severity: "Critical",
    status: "New",
    analyst: "Maya",
    tactic: "Initial Access",
    asset: "fin-admin-02",
    iocs: ["198.51.100.24", "mfa-fatigue"],
    slaHours: 2,
    createdAt: "2026-05-31T08:20:00Z",
    lastSentAt: ""
  },
  {
    id: "SOC-000002",
    title: "EDR detected credential dumping behavior",
    description: "Suspicious LSASS memory access from unsigned executable in user profile path.",
    source: "CrowdStrike",
    severity: "High",
    status: "Investigating",
    analyst: "Noah",
    tactic: "Credential Access",
    asset: "ENG-LT-442",
    iocs: ["temp_sync.exe", "T1003"],
    slaHours: 4,
    createdAt: "2026-05-31T07:35:00Z",
    lastSentAt: ""
  },
  {
    id: "SOC-000003",
    title: "Suspicious outbound DNS tunneling pattern",
    description: "Firewall analytics found high entropy DNS queries to a newly registered domain.",
    source: "Palo Alto",
    severity: "Medium",
    status: "Triage",
    analyst: "Priya",
    tactic: "Command and Control",
    asset: "10.32.14.88",
    iocs: ["updates-cdn-check.example", "dns-tunnel"],
    slaHours: 8,
    createdAt: "2026-05-30T22:10:00Z",
    lastSentAt: ""
  },
  {
    id: "SOC-000004",
    title: "Phishing message with blocked payload",
    description: "Email gateway quarantined a message containing a malicious HTML attachment.",
    source: "Proofpoint",
    severity: "Low",
    status: "Closed",
    analyst: "Elena",
    tactic: "Initial Access",
    asset: "mailbox:ap@company.local",
    iocs: ["invoice_may.html", "185.199.110.153"],
    slaHours: 24,
    createdAt: "2026-05-30T15:42:00Z",
    lastSentAt: "2026-05-30T16:05:00Z"
  }
];

const state = {
  view: "dashboard",
  detailAlertId: getRouteAlertId(),
  alerts: loadAlerts(),
  integration: loadIntegration(),
  filters: {
    search: "",
    severity: "all",
    status: "all",
    analyst: "all"
  }
};

const content = document.querySelector("#content");
const viewTitle = document.querySelector("#viewTitle");
const dialog = document.querySelector("#alertDialog");
const alertForm = document.querySelector("#alertForm");
const deleteAlertButton = document.querySelector("#deleteAlertButton");
const themeSelect = document.querySelector("#themeSelect");

applyTheme(loadTheme());

function loadAlerts() {
  const saved = localStorage.getItem(ALERT_STORAGE_KEY);
  if (!saved) return normalizeAlerts(seedAlerts);

  try {
    const parsed = JSON.parse(saved);
    return Array.isArray(parsed) ? normalizeAlerts(parsed) : normalizeAlerts(seedAlerts);
  } catch {
    return normalizeAlerts(seedAlerts);
  }
}

function loadIntegration() {
  const fallback = { webhookUrl: "", apiKey: "", headerName: "X-API-Key" };
  const saved = localStorage.getItem(INTEGRATION_STORAGE_KEY);
  if (!saved) return fallback;

  try {
    return { ...fallback, ...JSON.parse(saved) };
  } catch {
    return fallback;
  }
}

function loadTheme() {
  const saved = localStorage.getItem(THEME_STORAGE_KEY);
  return ["light", "dark", "system"].includes(saved) ? saved : "system";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  if (themeSelect) themeSelect.value = theme;
}

function saveTheme(theme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  applyTheme(theme);
}

function saveAlerts() {
  localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(state.alerts));
  saveAlertsToApi(state.alerts);
}

function saveIntegration() {
  localStorage.setItem(INTEGRATION_STORAGE_KEY, JSON.stringify(state.integration));
}

function filteredAlerts() {
  const query = state.filters.search.trim().toLowerCase();
  return state.alerts.filter((alert) => {
    const searchable = [
      alert.id,
      alert.title,
      alert.description,
      alert.source,
      alert.severity,
      alert.status,
      alert.analyst,
      alert.tactic,
      alert.asset,
      ...alert.iocs
    ].join(" ").toLowerCase();

    return (
      (!query || searchable.includes(query)) &&
      (state.filters.severity === "all" || alert.severity === state.filters.severity) &&
      (state.filters.status === "all" || alert.status === state.filters.status) &&
      (state.filters.analyst === "all" || alert.analyst === state.filters.analyst)
    );
  });
}

function render() {
  const routeAlertId = getRouteAlertId();
  state.detailAlertId = routeAlertId;
  if (routeAlertId) {
    document.body.classList.add("detail-mode");
    renderAlertDetail(routeAlertId);
    return;
  }

  document.body.classList.remove("detail-mode");
  viewTitle.textContent = titleForView(state.view);
  document.querySelector(".filters").hidden = false;
  renderAnalystFilter();

  const alerts = filteredAlerts();
  if (state.view === "dashboard") renderDashboard(alerts);
  if (state.view === "queue") renderQueue(alerts);
  if (state.view === "cases") renderCases(alerts);
  if (state.view === "automation") renderAutomation(alerts);
  if (state.view === "reports") renderReports(alerts);
  if (state.view === "settings") renderSettings();
}

function titleForView(view) {
  const titles = {
    dashboard: "SOC Dashboard",
    queue: "Alert Queue",
    cases: "Cases",
    automation: "n8n Automation",
    reports: "Reports",
    settings: "Settings"
  };
  return titles[view];
}

function renderAnalystFilter() {
  const select = document.querySelector("#analystFilter");
  const current = select.value;
  const analysts = [...new Set(state.alerts.map((alert) => alert.analyst).filter(Boolean))].sort();
  select.innerHTML = '<option value="all">All analysts</option>';
  analysts.forEach((analyst) => {
    const option = document.createElement("option");
    option.value = analyst;
    option.textContent = analyst;
    select.append(option);
  });
  select.value = analysts.includes(current) ? current : "all";
  state.filters.analyst = select.value;
}

function renderDashboard(alerts) {
  content.className = "content grid";
  const openAlerts = alerts.filter((alert) => alert.status !== "Closed");
  const critical = alerts.filter((alert) => alert.severity === "Critical").length;
  const overdue = alerts.filter(isOverdue).length;
  content.innerHTML = `
    <section class="metric-grid">
      <div class="metric"><strong>${alerts.length}</strong><span>Visible alerts</span></div>
      <div class="metric"><strong>${openAlerts.length}</strong><span>Open alerts</span></div>
      <div class="metric"><strong>${critical}</strong><span>Critical</span></div>
      <div class="metric"><strong>${overdue}</strong><span>SLA breached</span></div>
    </section>
    <section class="board">${STATUSES.map((status) => statusColumn(status, alerts)).join("")}</section>
  `;
}

function statusColumn(status, alerts) {
  const statusAlerts = alerts.filter((alert) => alert.status === status);
  const cards = statusAlerts.length
    ? statusAlerts.map(alertCardHtml).join("")
    : '<div class="empty">No alerts</div>';
  return `
    <section class="column">
      <header>
        <h2>${status}</h2>
        <span class="pill">${statusAlerts.length}</span>
      </header>
      <div class="issue-list">${cards}</div>
    </section>
  `;
}

function renderQueue(alerts) {
  content.className = "content grid";
  content.innerHTML = `
    <section class="panel">
      <h2>Alert queue</h2>
      <div class="table" id="alertTable"></div>
    </section>
  `;
  const table = document.querySelector("#alertTable");
  if (!alerts.length) {
    table.innerHTML = '<div class="empty">No matching alerts</div>';
    return;
  }
  alerts.forEach((alert) => {
    const row = document.createElement("div");
    row.className = "table-row alert-row";
    row.innerHTML = `
      <button type="button" data-edit="${alert.id}">${alert.id}</button>
      <strong>${escapeHtml(alert.title)}</strong>
      <span class="severity-${alert.severity}">${alert.severity}</span>
      <span>${alert.source}</span>
      <span>${alert.status}</span>
      <div class="row-actions">
        <button type="button" data-view-alert="${alert.id}">Open</button>
        <button type="button" data-copy-url="${alert.id}">Copy URL</button>
      </div>
    `;
    table.append(row);
  });
}

function renderCases(alerts) {
  content.className = "content grid";
  const cases = alerts.filter((alert) => ["Investigating", "Contained", "Closed"].includes(alert.status));
  content.innerHTML = `
    <section class="panel">
      <h2>Cases</h2>
      <div class="grid">${cases.length ? cases.map(alertCardHtml).join("") : '<div class="empty">No active cases</div>'}</div>
    </section>
  `;
}

function renderAutomation(alerts) {
  content.className = "content grid two-col";
  const recent = alerts.slice(0, 8);
  const webhookUrl = `${window.location.origin}/api/webhook/n8n`;
  content.innerHTML = `
    <section class="panel">
      <h2>Inbound n8n webhook</h2>
      <form id="integrationForm" class="settings-form">
        <label>
          Tracker webhook URL
          <input id="webhookUrl" readonly value="${escapeHtml(webhookUrl)}">
        </label>
        <label>
          API key expected by tracker
          <input id="apiKey" type="password" autocomplete="off" value="${escapeHtml(state.integration.apiKey || "change-me")}">
        </label>
        <label>
          Header name
          <input id="headerName" value="${escapeHtml(state.integration.headerName)}">
        </label>
        <div class="setting-row">
          <button class="primary" type="submit">Save display settings</button>
          <button id="copyWebhookButton" type="button">Copy webhook URL</button>
        </div>
      </form>
      <p id="integrationStatus" class="muted">Configure n8n to POST alert JSON here. The server validates the API key header.</p>
    </section>
    <section class="panel">
      <h2>Recent inbound alerts</h2>
      <div class="grid">
        ${recent.length ? recent.map((alert) => `<div class="release-row"><strong>${alert.id}</strong><span>${escapeHtml(alert.title)}</span><span class="pill">${formatDate(alert.createdAt)}</span></div>`).join("") : '<div class="empty">No inbound alerts yet</div>'}
      </div>
    </section>
  `;
}

function renderReports(alerts) {
  content.className = "content grid two-col";
  content.innerHTML = `
    <section class="panel">
      <h2>Severity split</h2>
      <div class="grid">
        ${SEVERITIES.map((severity) => progressLine(severity, alerts.filter((alert) => alert.severity === severity).length, alerts.length)).join("")}
      </div>
    </section>
    <section class="panel">
      <h2>Source split</h2>
      <div class="grid">
        ${Object.entries(groupBy(alerts, "source")).map(([source, sourceAlerts]) => progressLine(source, sourceAlerts.length, alerts.length)).join("") || '<div class="empty">No alerts</div>'}
      </div>
    </section>
  `;
}

function renderSettings() {
  content.className = "content grid";
  content.innerHTML = `
    <section class="panel">
      <h2>Data</h2>
      <div class="grid">
        <div class="settings-form">
          <label>
            Paste Elastic alert JSON
            <textarea id="elasticJsonInput" class="json-paste" rows="10" placeholder='{"_source":{"kibana.alert.rule.name":"Suspicious login","event.severity":70}}'></textarea>
          </label>
          <div class="setting-row">
            <button id="parseElasticButton" class="primary" type="button">Add parsed alert</button>
            <button id="clearElasticButton" type="button">Clear</button>
          </div>
          <p id="elasticParseStatus" class="muted">Paste a single Elastic alert, a hit with _source, or a hits.hits response.</p>
        </div>
        <div class="setting-row">
          <button id="exportButton" type="button">Export JSON</button>
          <label>
            Import JSON
            <input id="importInput" type="file" accept="application/json">
          </label>
        </div>
        <p class="muted">Alerts and n8n settings are stored in this browser with localStorage.</p>
      </div>
    </section>
  `;
}

function alertCardHtml(alert) {
  return `
    <article class="issue-card">
      <div class="card-top">
        <span class="card-key">${alert.id}</span>
        <span class="pill severity-pill severity-${alert.severity}">${alert.severity}</span>
        ${isOverdue(alert) ? '<span class="pill overdue">SLA</span>' : ""}
      </div>
      <p class="card-title">${escapeHtml(alert.title)}</p>
      <div class="pill-row">
        <span class="pill">${escapeHtml(alert.source)}</span>
        <span class="pill">${escapeHtml(alert.tactic)}</span>
      </div>
      <div class="card-meta">
        <span>${escapeHtml(alert.analyst || "Unassigned")}</span>
        <span>${escapeHtml(alert.asset)}</span>
        <span>${formatDate(alert.createdAt)}</span>
      </div>
      <div class="card-actions">
        <button type="button" data-view-alert="${alert.id}">Open</button>
        <button type="button" data-edit="${alert.id}">Edit</button>
      </div>
    </article>
  `;
}

function renderAlertDetail(alertId) {
  const alert = state.alerts.find((item) => item.id === alertId);
  viewTitle.textContent = alert ? alert.id : "Alert not found";
  document.querySelector(".filters").hidden = true;
  activateNav();
  content.className = "content grid";

  if (!alert) {
    content.innerHTML = `
      <section class="panel detail-panel">
        <div class="detail-actions">
          <button type="button" data-back-to-dashboard>Back</button>
        </div>
        <h2>Alert not found</h2>
        <p class="muted">The alert link does not match a saved alert in this browser.</p>
      </section>
    `;
    return;
  }

  const reportUrl = alertUrl(alert.id);
  content.innerHTML = `
    <section class="panel detail-panel">
      <div class="detail-actions">
        <button type="button" data-back-to-dashboard>Back</button>
        <button type="button" data-edit="${alert.id}">Edit</button>
        <button type="button" data-copy-url="${alert.id}">Copy URL</button>
      </div>
      <p class="eyebrow">Alert detail</p>
      <h2>${escapeHtml(alert.title)}</h2>
      <div class="pill-row">
        <span class="card-key">${alert.id}</span>
        <span class="pill severity-pill severity-${alert.severity}">${alert.severity}</span>
        <span class="pill">${escapeHtml(alert.status)}</span>
        <span class="pill">${escapeHtml(alert.source)}</span>
        ${isOverdue(alert) ? '<span class="pill overdue">SLA breached</span>' : ""}
      </div>
      <div class="detail-grid">
        <div><strong>Analyst</strong><span>${escapeHtml(alert.analyst)}</span></div>
        <div><strong>Asset</strong><span>${escapeHtml(alert.asset)}</span></div>
        <div><strong>MITRE tactic</strong><span>${escapeHtml(alert.tactic)}</span></div>
        <div><strong>SLA</strong><span>${alert.slaHours} hours</span></div>
        <div><strong>Created</strong><span>${formatDate(alert.createdAt)}</span></div>
        <div><strong>Last updated</strong><span>${formatDate(alert.createdAt)}</span></div>
      </div>
      <section class="detail-section">
        <h3>Description</h3>
        <p class="description-full">${escapeHtml(alert.description || "No description provided.")}</p>
      </section>
      <section class="detail-section">
        <h3>IOCs</h3>
        <div class="pill-row">${alert.iocs.length ? alert.iocs.map((ioc) => `<span class="pill">${escapeHtml(ioc)}</span>`).join("") : '<span class="muted">No IOCs</span>'}</div>
      </section>
      <section class="detail-section">
        <h3>Report URL</h3>
        <div class="copy-line">
          <input readonly value="${escapeHtml(reportUrl)}">
          <button type="button" data-copy-url="${alert.id}">Copy</button>
        </div>
      </section>
    </section>
  `;
}

function progressLine(label, count, total) {
  const percent = total ? Math.round((count / total) * 100) : 0;
  return `<div><strong>${escapeHtml(label)}</strong><div class="progress"><span style="width: ${percent}%"></span></div><p class="muted">${count} alerts</p></div>`;
}

function openAlertDialog(alert = null) {
  document.querySelector("#dialogTitle").textContent = alert ? `Edit ${alert.id}` : "New alert";
  document.querySelector("#alertId").value = alert?.id || "";
  document.querySelector("#title").value = alert?.title || "";
  document.querySelector("#description").value = alert?.description || "";
  document.querySelector("#source").value = alert?.source || "";
  document.querySelector("#severity").value = alert?.severity || "Medium";
  document.querySelector("#status").value = alert?.status || "New";
  document.querySelector("#analyst").value = alert?.analyst || "";
  document.querySelector("#tactic").value = alert?.tactic || "";
  document.querySelector("#asset").value = alert?.asset || "";
  document.querySelector("#slaHours").value = alert?.slaHours || 8;
  document.querySelector("#iocs").value = alert?.iocs?.join(", ") || "";
  deleteAlertButton.hidden = !alert;
  dialog.showModal();
  autoSizeTextArea(document.querySelector("#description"));
}

function saveAlertFromForm() {
  const id = document.querySelector("#alertId").value || nextAlertId();
  const existing = state.alerts.find((alert) => alert.id === id);
  const alert = {
    id,
    title: document.querySelector("#title").value.trim(),
    description: document.querySelector("#description").value.trim(),
    source: document.querySelector("#source").value.trim() || "Manual",
    severity: document.querySelector("#severity").value,
    status: document.querySelector("#status").value,
    analyst: document.querySelector("#analyst").value.trim() || "Unassigned",
    tactic: document.querySelector("#tactic").value.trim() || "Unknown",
    asset: document.querySelector("#asset").value.trim() || "Unknown",
    iocs: document.querySelector("#iocs").value.split(",").map((ioc) => ioc.trim()).filter(Boolean),
    slaHours: Number(document.querySelector("#slaHours").value || 8),
    createdAt: existing?.createdAt || new Date().toISOString(),
    lastSentAt: existing?.lastSentAt || ""
  };

  const existingIndex = state.alerts.findIndex((item) => item.id === id);
  if (existingIndex >= 0) {
    state.alerts[existingIndex] = alert;
  } else {
    state.alerts.unshift(alert);
  }
  saveAlerts();
  if (state.detailAlertId === alert.id) {
    window.location.hash = alertRoute(alert.id);
  }
  render();
}

function setIntegrationStatus(message, isError) {
  const status = document.querySelector("#integrationStatus");
  if (!status) {
    alert(message);
    return;
  }
  status.textContent = message;
  status.classList.toggle("error", isError);
}

function nextAlertId() {
  return formatAlertId(highestAlertNumber(state.alerts) + 1);
}

function highestAlertNumber(alerts) {
  return alerts.reduce((highest, alert) => {
    const number = alertNumber(alert.id);
    return Number.isFinite(number) ? Math.max(highest, number) : highest;
  }, 0);
}

function normalizeAlerts(alerts) {
  return alerts.map((alert, index) => ({
    id: normalizeAlertId(alert.id, index),
    title: alert.title || alert.summary || "Untitled alert",
    description: alert.description || "",
    source: alert.source || "Manual",
    severity: SEVERITIES.includes(alert.severity) ? alert.severity : normalizeSeverity(alert.priority),
    status: STATUSES.includes(alert.status) ? alert.status : normalizeStatus(alert.status),
    analyst: alert.analyst || alert.assignee || "Unassigned",
    tactic: alert.tactic || "Unknown",
    asset: alert.asset || "Unknown",
    iocs: Array.isArray(alert.iocs) ? alert.iocs : Array.isArray(alert.labels) ? alert.labels : [],
    slaHours: Number(alert.slaHours || 8),
    createdAt: alert.createdAt || new Date().toISOString(),
    lastSentAt: alert.lastSentAt || ""
  }));
}

function parseElasticJsonToAlerts(raw) {
  const parsed = JSON.parse(raw);
  const records = elasticRecords(parsed);
  if (!records.length) throw new Error("No alert records found");
  const start = highestAlertNumber(state.alerts);
  return records.map((record, index) => normalizeAlerts([{
    ...elasticRecordToAlert(record),
    id: formatAlertId(start + index + 1)
  }])[0]);
}

function elasticRecords(value) {
  if (Array.isArray(value)) return value.flatMap(elasticRecords);
  if (!value || typeof value !== "object") return [];
  if (Array.isArray(value.hits?.hits)) return value.hits.hits.flatMap(elasticRecords);
  if (value._source && typeof value._source === "object") return [{ ...value._source, _id: value._id, _index: value._index }];
  if (value.alert && typeof value.alert === "object") return [value.alert];
  return [value];
}

function elasticRecordToAlert(record) {
  const title = firstValue(record, [
    "kibana.alert.rule.name",
    "signal.rule.name",
    "rule.name",
    "event.action",
    "event.kind",
    "message",
    "title",
    "name"
  ]);
  const description = firstValue(record, [
    "kibana.alert.reason",
    "kibana.alert.rule.description",
    "signal.reason",
    "rule.description",
    "message",
    "description"
  ]);
  const severity = normalizeElasticSeverity(firstValue(record, [
    "kibana.alert.severity",
    "signal.rule.severity",
    "rule.severity",
    "event.severity",
    "log.level",
    "severity"
  ]));
  const tactic = firstValue(record, [
    "kibana.alert.rule.threat.tactic.name",
    "signal.rule.threat.tactic.name",
    "threat.tactic.name",
    "rule.threat.tactic.name"
  ]);
  const asset = firstValue(record, [
    "host.name",
    "host.hostname",
    "agent.name",
    "observer.name",
    "user.name",
    "source.ip",
    "destination.ip",
    "asset"
  ]);
  const iocs = uniqueValues([
    ...valuesFor(record, ["source.ip", "destination.ip", "client.ip", "server.ip", "host.ip", "related.ip"]),
    ...valuesFor(record, ["url.domain", "dns.question.name", "destination.domain", "related.hosts"]),
    ...valuesFor(record, ["file.hash.sha256", "file.hash.sha1", "file.hash.md5", "process.hash.sha256", "related.hash"]),
    ...valuesFor(record, ["user.name", "source.user.name", "destination.user.name"])
  ]);

  return {
    id: "",
    title: title || "Elastic alert",
    description: description || "Imported from Elastic JSON.",
    source: firstValue(record, ["event.module", "event.dataset", "data_stream.dataset", "_index"]) || "Elastic",
    severity,
    status: "New",
    analyst: "Unassigned",
    tactic: tactic || "Unknown",
    asset: asset || "Unknown",
    iocs,
    slaHours: severity === "Critical" ? 2 : severity === "High" ? 4 : severity === "Medium" ? 8 : 24,
    createdAt: firstValue(record, ["@timestamp", "event.created", "kibana.alert.start"]) || new Date().toISOString(),
    lastSentAt: ""
  };
}

function firstValue(record, paths) {
  for (const path of paths) {
    const values = valuesFor(record, [path]);
    if (values.length) return values[0];
  }
  return "";
}

function valuesFor(record, paths) {
  return paths.flatMap((path) => flattenValue(readPath(record, path))).filter((value) => value !== "");
}

function readPath(record, path) {
  if (Object.prototype.hasOwnProperty.call(record, path)) return record[path];
  return path.split(".").reduce((value, key) => {
    if (Array.isArray(value)) return value.map((item) => item?.[key]).filter((item) => item !== undefined);
    return value && typeof value === "object" ? value[key] : undefined;
  }, record);
}

function flattenValue(value) {
  if (value === undefined || value === null) return [];
  if (Array.isArray(value)) return value.flatMap(flattenValue);
  if (typeof value === "object") {
    if ("name" in value) return flattenValue(value.name);
    if ("ip" in value) return flattenValue(value.ip);
    return [];
  }
  return [String(value).trim()].filter(Boolean);
}

function uniqueValues(values) {
  return [...new Set(values.filter(Boolean))];
}

function normalizeElasticSeverity(value) {
  const text = String(value || "").toLowerCase();
  const number = Number(value);
  if (["critical", "fatal"].includes(text) || number >= 70) return "Critical";
  if (["high", "error"].includes(text) || number >= 50) return "High";
  if (["medium", "warning", "warn"].includes(text) || number >= 20) return "Medium";
  return "Low";
}

function normalizeSeverity(value) {
  if (value === "Highest") return "Critical";
  if (value === "High") return "High";
  if (value === "Low") return "Low";
  return "Medium";
}

function normalizeStatus(value) {
  const map = {
    "To Do": "New",
    "In Progress": "Investigating",
    Review: "Contained",
    Done: "Closed"
  };
  return map[value] || "New";
}

function groupBy(items, key) {
  return items.reduce((groups, item) => {
    const group = item[key] || "Unknown";
    groups[group] = groups[group] || [];
    groups[group].push(item);
    return groups;
  }, {});
}

function normalizeAlertId(id, index) {
  const number = alertNumber(id);
  if (!Number.isFinite(number)) return formatAlertId(index + 1);
  const migratedNumber = number >= 1001 && number <= 1999 ? number - 1000 : number;
  return formatAlertId(migratedNumber);
}

function alertNumber(id) {
  const match = String(id || "").match(/(\d+)$/);
  return match ? Number(match[1]) : NaN;
}

function formatAlertId(number) {
  return `SOC-${String(number).padStart(6, "0")}`;
}

function getRouteAlertId() {
  const match = window.location.hash.match(/^#alert\/([^/?#]+)$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function alertRoute(alertId) {
  return `#alert/${encodeURIComponent(alertId)}`;
}

function alertUrl(alertId) {
  return `${window.location.origin}${window.location.pathname}${alertRoute(alertId)}`;
}

async function copyAlertUrl(alertId) {
  const url = alertUrl(alertId);
  try {
    await navigator.clipboard.writeText(url);
    showToast(`Copied ${alertId} URL.`);
  } catch {
    const field = document.createElement("textarea");
    field.value = url;
    document.body.append(field);
    field.select();
    document.execCommand("copy");
    field.remove();
    showToast(`Copied ${alertId} URL.`);
  }
}

function showToast(message) {
  let toast = document.querySelector("#toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.append(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2200);
}

function autoSizeTextArea(textarea) {
  if (!textarea) return;
  textarea.style.height = "auto";
  textarea.style.height = `${textarea.scrollHeight}px`;
}

async function loadAlertsFromApi() {
  try {
    const response = await fetch(`${API_BASE}/api/alerts`, { cache: "no-store" });
    if (!response.ok) return;
    const alerts = await response.json();
    if (!Array.isArray(alerts)) return;
    state.alerts = normalizeAlerts(alerts.length ? alerts : seedAlerts);
    localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(state.alerts));
    render();
  } catch {
    // Static-file fallback keeps localStorage behavior when server.py is not used.
  }
}

async function saveAlertsToApi(alerts) {
  try {
    await fetch(`${API_BASE}/api/alerts`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(alerts)
    });
  } catch {
    // Ignore when opened as a static file or served without the API.
  }
}

function isOverdue(alert) {
  if (alert.status === "Closed") return false;
  const dueAt = new Date(alert.createdAt).getTime() + Number(alert.slaHours || 8) * 60 * 60 * 1000;
  return Date.now() > dueAt;
}

function formatDate(value) {
  if (!value) return "Never";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character]);
}

function activateNav() {
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", !state.detailAlertId && item.dataset.view === state.view);
  });
}

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    if (window.location.hash) {
      window.location.hash = "";
    }
    state.view = button.dataset.view;
    activateNav();
    render();
  });
});

document.querySelector("#searchInput").addEventListener("input", (event) => {
  state.filters.search = event.target.value;
  render();
});

document.querySelector("#severityFilter").addEventListener("change", (event) => {
  state.filters.severity = event.target.value;
  render();
});

document.querySelector("#statusFilter").addEventListener("change", (event) => {
  state.filters.status = event.target.value;
  render();
});

document.querySelector("#analystFilter").addEventListener("change", (event) => {
  state.filters.analyst = event.target.value;
  render();
});

document.querySelector("#newAlertButton").addEventListener("click", () => openAlertDialog());

themeSelect.addEventListener("change", (event) => {
  saveTheme(event.target.value);
});

document.querySelector("#resetDemo").addEventListener("click", () => {
  state.alerts = normalizeAlerts(seedAlerts);
  saveAlerts();
  render();
});

content.addEventListener("click", (event) => {
  const editButton = event.target.closest("[data-edit]");
  const viewButton = event.target.closest("[data-view-alert]");
  const copyButton = event.target.closest("[data-copy-url]");
  const backButton = event.target.closest("[data-back-to-dashboard]");

  if (editButton) {
    const alertItem = state.alerts.find((item) => item.id === editButton.dataset.edit);
    if (alertItem) openAlertDialog(alertItem);
  }

  if (viewButton) {
    window.location.hash = alertRoute(viewButton.dataset.viewAlert);
  }

  if (copyButton) {
    copyAlertUrl(copyButton.dataset.copyUrl);
  }

  if (backButton) {
    window.location.hash = "";
  }

});

alertForm.addEventListener("submit", (event) => {
  event.preventDefault();
  saveAlertFromForm();
  dialog.close();
});

alertForm.addEventListener("click", (event) => {
  if (!event.target.closest("[data-close-dialog]")) return;
  dialog.close();
});

document.querySelector("#description").addEventListener("input", (event) => {
  autoSizeTextArea(event.target);
});

deleteAlertButton.addEventListener("click", () => {
  const id = document.querySelector("#alertId").value;
  state.alerts = state.alerts.filter((alert) => alert.id !== id);
  saveAlerts();
  dialog.close();
  render();
});

document.addEventListener("submit", (event) => {
  if (event.target.id !== "integrationForm") return;
  event.preventDefault();
  state.integration = {
    webhookUrl: document.querySelector("#webhookUrl").value.trim(),
    apiKey: document.querySelector("#apiKey").value.trim(),
    headerName: document.querySelector("#headerName").value.trim() || "X-API-Key"
  };
  saveIntegration();
  setIntegrationStatus("Webhook display settings saved. Server API key is configured with N8N_API_KEY.", false);
});

document.addEventListener("click", (event) => {
  if (event.target.id === "exportButton") {
    const blob = new Blob([JSON.stringify(state.alerts, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "soc-alerts.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  if (event.target.id === "copyWebhookButton") {
    navigator.clipboard.writeText(document.querySelector("#webhookUrl").value);
    showToast("Copied webhook URL.");
  }

  if (event.target.id === "clearElasticButton") {
    document.querySelector("#elasticJsonInput").value = "";
    const status = document.querySelector("#elasticParseStatus");
    status.textContent = "Paste a single Elastic alert, a hit with _source, or a hits.hits response.";
    status.classList.remove("error");
  }

  if (event.target.id === "parseElasticButton") {
    const input = document.querySelector("#elasticJsonInput");
    const status = document.querySelector("#elasticParseStatus");
    try {
      const parsedAlerts = parseElasticJsonToAlerts(input.value.trim());
      state.alerts = [...parsedAlerts, ...state.alerts];
      saveAlerts();
      input.value = "";
      render();
      showToast(`Added ${parsedAlerts.length} parsed alert${parsedAlerts.length === 1 ? "" : "s"}.`);
    } catch (error) {
      status.textContent = `Parse failed: ${error.message}`;
      status.classList.add("error");
    }
  }
});

document.addEventListener("change", (event) => {
  if (event.target.id !== "importInput") return;
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const imported = JSON.parse(reader.result);
      if (!Array.isArray(imported)) throw new Error("Expected an array");
      state.alerts = normalizeAlerts(imported);
      saveAlerts();
      render();
    } catch {
      alert("Import failed. Please choose a valid SOC alerts JSON file.");
    }
  };
  reader.readAsText(file);
});

window.addEventListener("hashchange", render);

render();
loadAlertsFromApi();
window.setInterval(loadAlertsFromApi, 5000);
