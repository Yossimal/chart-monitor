/**
 * Chart-Monitor Frontend – Vanilla JS
 *
 * Polls /api/v1/dashboards for the list, then polls each selected dashboard
 * at its scrape_interval_seconds. All DOM is built with semantic CSS classes
 * defined in styles.css. No utility frameworks required.
 */

const API_BASE = "http://localhost:8000";

// ── State ─────────────────────────────────────────────────────────────────────
let currentDashboardId = null;
let pollingTimer = null;
let reconnectTimer = null;
let isConnected = false;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $bannerDisc = document.getElementById("banner-disconnected");
const $bannerConn = document.getElementById("banner-connecting");
const $navList = document.getElementById("dashboard-list");
const $content = document.getElementById("dashboard-content");
const $lastUpdated = document.getElementById("last-updated");
const $statusDot = document.getElementById("status-dot");

// ── Connection state ──────────────────────────────────────────────────────────

function setConnected(ok) {
    isConnected = ok;
    if (ok) {
        $bannerDisc.classList.add("hidden");
        $bannerConn.classList.add("hidden");
        $statusDot.className = "status-dot status-dot--ok";
    } else {
        $bannerDisc.classList.remove("hidden");
        $statusDot.className = "status-dot status-dot--error";
    }
}

function showConnecting() {
    $bannerConn.classList.remove("hidden");
    $bannerDisc.classList.add("hidden");
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────

async function apiFetch(path) {
    const resp = await fetch(API_BASE + path);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
    return resp.json();
}

// ── Dashboard list ────────────────────────────────────────────────────────────

async function loadDashboardList() {
    try {
        const dashboards = await apiFetch("/api/v1/dashboards");
        setConnected(true);
        renderSidebar(dashboards);
        if (dashboards.length > 0 && !currentDashboardId) {
            selectDashboard(dashboards[0].id, dashboards[0].scrape_interval_seconds);
        }
    } catch (_err) {
        setConnected(false);
        $navList.innerHTML = `<span style="font-size:.72rem; color: var(--color-red); padding: 4px 10px;">Cannot reach server</span>`;
        scheduleReconnect();
    }
}

function renderSidebar(dashboards) {
    if (dashboards.length === 0) {
        $navList.innerHTML = `<span style="font-size:.72rem; color: var(--color-text-xs); padding: 4px 10px; font-style:italic;">No dashboards</span>`;
        return;
    }
    $navList.innerHTML = dashboards.map(d => `
    <button
      id="nav-${d.id}"
      class="nav-btn"
      onclick="selectDashboard('${esc(d.id)}', ${d.scrape_interval_seconds})"
    >${esc(d.name)}</button>`
    ).join("");
}

// ── Dashboard selection ───────────────────────────────────────────────────────

function selectDashboard(dashboardId, scrapeInterval) {
    // De-activate old button
    if (currentDashboardId) {
        const old = document.getElementById(`nav-${currentDashboardId}`);
        if (old) old.classList.remove("nav-btn--active");
    }
    currentDashboardId = dashboardId;
    clearInterval(pollingTimer);

    // Activate new button
    const btn = document.getElementById(`nav-${dashboardId}`);
    if (btn) btn.classList.add("nav-btn--active");

    fetchAndRender(dashboardId);
    pollingTimer = setInterval(() => fetchAndRender(dashboardId), scrapeInterval * 1000);
}

// ── Data fetch & render ───────────────────────────────────────────────────────

async function fetchAndRender(dashboardId) {
    if (!isConnected) return;
    try {
        const data = await apiFetch(`/api/v1/dashboards/${dashboardId}/data`);
        setConnected(true);
        renderDashboard(data);
        $lastUpdated.textContent = new Date().toLocaleTimeString();
    } catch (_err) {
        setConnected(false);
        showConnecting();
        scheduleReconnect();
    }
}

function renderDashboard(data) {
    // Dashboard-level error
    if (data.error) {
        $content.innerHTML = `
      <div class="dashboard-card dashboard-card--error">
        <div class="dashboard-header">
          <span class="dashboard-name">${esc(data.dashboard_id)}</span>
        </div>
        <div class="error-block">
          <div class="error-label">⚠ Dashboard Error</div>
          <pre class="error-text">${esc(data.error)}</pre>
        </div>
      </div>`;
        return;
    }

    if (!data.columns || data.columns.length === 0) {
        $content.innerHTML = `<div class="empty-state">No data returned</div>`;
        return;
    }

    const thead = `<tr>${data.columns.map(c => `<th>${esc(c)}</th>`).join("")}</tr>`;

    const tbody = data.rows.map(row => {
        const cells = data.columns.map(col => {
            const cell = row[col] || { value: "", style: "" };
            // style field is raw CSS string: "color: #ef4444; font-weight: bold;"
            const styleAttr = cell.style ? ` style="${esc(cell.style)}"` : "";
            // Also support special class markers like "cell-error"
            const classAttr = (cell.style === "cell-error") ? ` class="cell-error"` : "";
            return `<td${classAttr}${styleAttr}>${esc(String(cell.value))}</td>`;
        }).join("");
        return `<tr>${cells}</tr>`;
    }).join("");

    $content.innerHTML = `
    <div class="dashboard-card">
      <div class="dashboard-header">
        <span class="dashboard-name">${esc(data.dashboard_id)}</span>
        <span class="dashboard-meta">${data.rows.length} row(s) · refresh ${data.scrape_interval_seconds}s</span>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>${thead}</thead>
          <tbody>${tbody}</tbody>
        </table>
      </div>
    </div>`;
}

// ── Reconnect ─────────────────────────────────────────────────────────────────

function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(async () => {
        reconnectTimer = null;
        showConnecting();
        await loadDashboardList();
        if (isConnected && currentDashboardId) fetchAndRender(currentDashboardId);
    }, 5000);
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function esc(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// ── Boot ──────────────────────────────────────────────────────────────────────
loadDashboardList();
