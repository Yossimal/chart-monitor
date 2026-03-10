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
let currentScrapeInterval = 30;
let maxDataValue = 10000;
let cachedDashboards = [];

// ── Table State ───────────────────────────────────────────────────────────────
let rawData = { columns: [], rows: [] };
let tableState = {
    sortColumn: null,
    sortDirection: 'asc',
    filterText: '',
    currentPage: 0,
    pageSize: 50
};

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $bannerDisc = document.getElementById("banner-disconnected");
const $bannerConn = document.getElementById("banner-connecting");
const $navList = document.getElementById("dashboard-list");
const $content = document.getElementById("dashboard-content");
const $lastUpdated = document.getElementById("last-updated");
const $statusDot = document.getElementById("status-dot");
const $dashboardSearchInput = document.getElementById("dashboardSearchInput");
const $syncAlert = document.getElementById("sync-alert");
const $gitopsUnconfigured = document.getElementById("gitops-unconfigured");
const $appMainWrapper = document.getElementById("app-main-wrapper");

// ── GitOps Setup Page ─────────────────────────────────────────────────────────

function switchGitTab(provider) {
    ["github", "gitlab", "bitbucket"].forEach(p => {
        document.getElementById(`guide-${p}`).classList.add("hidden");
        document.getElementById(`tab-${p}`).classList.remove("git-tab--active");
    });
    document.getElementById(`guide-${provider}`).classList.remove("hidden");
    document.getElementById(`tab-${provider}`).classList.add("git-tab--active");
}

async function checkGitOpsStatus() {
    try {
        const resp = await fetch(`${API_BASE}/api/v1/git/status`);
        if (!resp.ok) throw new Error("Status endpoint failed");
        const data = await resp.json();
        if (data.enabled) {
            $gitopsUnconfigured.classList.add("hidden");
            $appMainWrapper.classList.remove("hidden");
        } else {
            $gitopsUnconfigured.classList.remove("hidden");
            $appMainWrapper.classList.add("hidden");
        }
    } catch (_e) {
        // If backend is unreachable, assume GitOps is disabled and stay on setup page
        $gitopsUnconfigured.classList.remove("hidden");
        $appMainWrapper.classList.add("hidden");
    }
}

// ── GitOps Sync Modal ─────────────────────────────────────────────────────────

const STORAGE_KEY_SECRET = "cm-sync-secret";

function openSyncModal() {
    const saved = localStorage.getItem(STORAGE_KEY_SECRET);
    const input = document.getElementById("sync-secret-input");
    const remember = document.getElementById("sync-remember-checkbox");
    if (saved) {
        input.value = saved;
        remember.checked = true;
    } else {
        input.value = "";
        remember.checked = false;
    }
    document.getElementById("sync-modal").classList.remove("hidden");
    setTimeout(() => input.focus(), 50);
}

function closeSyncModal() {
    document.getElementById("sync-modal").classList.add("hidden");
}

function showSyncAlert(success, message, details) {
    if (!$syncAlert) return;
    const icon = success ? "✅" : "❌";
    const colorClass = success ? "sync-alert--success" : "sync-alert--error";
    $syncAlert.className = `sync-alert ${colorClass}`;
    $syncAlert.innerHTML = `
        <strong>${icon} ${success ? "Sync Successful" : "Sync Failed"}</strong>
        <span>${message}</span>
        ${details ? `<pre class="sync-alert-detail">${details}</pre>` : ""}
        <button class="sync-alert-close" onclick="this.parentElement.classList.add('hidden')" aria-label="Dismiss">✕</button>
    `;
    $syncAlert.classList.remove("hidden");
    // Auto-dismiss on success after 8 seconds
    if (success) {
        setTimeout(() => $syncAlert.classList.add("hidden"), 8000);
    }
}

async function submitSync() {
    const input = document.getElementById("sync-secret-input");
    const remember = document.getElementById("sync-remember-checkbox");
    const submitBtn = document.getElementById("sync-submit-btn");
    const secret = input.value.trim();

    if (!secret) {
        input.focus();
        return;
    }

    // Persist or clear from localStorage
    if (remember.checked) {
        localStorage.setItem(STORAGE_KEY_SECRET, secret);
    } else {
        localStorage.removeItem(STORAGE_KEY_SECRET);
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Syncing…";

    try {
        const resp = await fetch(`${API_BASE}/api/v1/git/sync`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${secret}`,
                "Content-Type": "application/json",
            },
        });

        const data = await resp.json();

        if (resp.ok && data.success) {
            closeSyncModal();
            showSyncAlert(true, data.message, data.details);
            // Reload dashboard list after successful sync
            await loadDashboardList();
        } else {
            // Show error in the alert and keep modal open
            closeSyncModal();
            const errorMsg = resp.status === 401
                ? "Invalid SYNC_SECRET. Please check your credentials."
                : (data.detail || data.message || `Server returned ${resp.status}`);
            showSyncAlert(false, errorMsg, data.details || "");
        }
    } catch (err) {
        closeSyncModal();
        showSyncAlert(false, "Network error during sync.", err.message || "");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sync";
    }
}

// ── Search Listeners ──────────────────────────────────────────────────────────
if ($dashboardSearchInput) {
    $dashboardSearchInput.addEventListener("input", (e) => {
        renderSidebar(cachedDashboards, e.target.value);
    });
}

// ── Connection state ──────────────────────────────────────────────────────────

function setConnected(ok) {
    isConnected = ok;
    if ($bannerDisc && $bannerConn && $statusDot) {
        if (ok) {
            $bannerDisc.classList.add("hidden");
            $bannerConn.classList.add("hidden");
            $statusDot.className = "status-dot status-dot--ok";
        } else {
            $bannerDisc.classList.remove("hidden");
            $statusDot.className = "status-dot status-dot--error";
        }
    }
}

function showConnecting() {
    if ($bannerConn && $bannerDisc) {
        $bannerConn.classList.remove("hidden");
        $bannerDisc.classList.add("hidden");
    }
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
        cachedDashboards = dashboards;
        renderSidebar(dashboards);
        if (dashboards.length > 0 && !currentDashboardId) {
            selectDashboard(dashboards[0].id, dashboards[0].scrape_interval_seconds);
        }
    } catch (_err) {
        setConnected(false);
        if ($navList) {
            $navList.innerHTML = `<span style="font-size:.72rem; color: var(--color-red); padding: 4px 10px;">Cannot reach server</span>`;
        }
        scheduleReconnect();
    }
}

function renderSidebar(dashboards, filterText = "") {
    if (!$navList) return;
    let filtered = dashboards;
    if (filterText) {
        const lower = filterText.toLowerCase();
        filtered = dashboards.filter(d =>
            (d.name && d.name.toLowerCase().includes(lower)) ||
            (d.id && d.id.toLowerCase().includes(lower))
        );
    }

    if (filtered.length === 0) {
        $navList.innerHTML = `<span style="font-size:.72rem; color: var(--color-text-xs); padding: 4px 10px; font-style:italic;">No dashboards found</span>`;
        return;
    }

    $navList.innerHTML = filtered.map(d => {
        const isActive = d.id === currentDashboardId ? " nav-btn--active" : "";
        const displayName = d.dashboard_name || d.name;
        return `
    <button
      id="nav-${d.id}"
      class="nav-btn${isActive}"
      onclick="selectDashboard('${esc(d.id)}', ${d.scrape_interval_seconds})"
    >${esc(displayName)}</button>`;
    }).join("");
}

// ── Dashboard selection ───────────────────────────────────────────────────────

function selectDashboard(dashboardId, scrapeInterval) {
    if (currentDashboardId) {
        const old = document.getElementById(`nav-${currentDashboardId}`);
        if (old) old.classList.remove("nav-btn--active");
    }
    currentDashboardId = dashboardId;
    clearInterval(pollingTimer);

    const btn = document.getElementById(`nav-${dashboardId}`);
    if (btn) btn.classList.add("nav-btn--active");

    currentScrapeInterval = scrapeInterval || 30;

    tableState.sortColumn = null;
    tableState.sortDirection = 'asc';
    tableState.filterText = '';
    tableState.currentPage = 0;

    fetchAndRender(dashboardId);
    startPolling();
}

function startPolling() {
    clearInterval(pollingTimer);
    if (!currentDashboardId || currentScrapeInterval <= 0) return;
    pollingTimer = setInterval(() => fetchAndRender(currentDashboardId), currentScrapeInterval * 1000);
}

// ── Manual Controls ───────────────────────────────────────────────────────────

function handleRefresh() {
    if (currentDashboardId) {
        fetchAndRender(currentDashboardId);
        startPolling();
    }
}

function handleIntervalChange(val) {
    const num = parseInt(val, 10);
    if (!isNaN(num)) {
        currentScrapeInterval = num;
        startPolling();
    }
}

function handleMaxChange(val) {
    let num = parseInt(val, 10);
    if (isNaN(num)) num = 10000;
    maxDataValue = num;
    if (currentDashboardId) {
        renderProcessedTable();
    }
}

// ── Theme State ───────────────────────────────────────────────────────────────

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("cm-theme", next);
    updateThemeIcon(next);
}

function initTheme() {
    const saved = localStorage.getItem("cm-theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
    updateThemeIcon(saved);
}

function updateThemeIcon(theme) {
    const btn = document.getElementById("theme-toggle-btn");
    if (btn) btn.textContent = theme === "dark" ? "☀️ Light" : "🌙 Dark";
}

// ── Data fetch & render ───────────────────────────────────────────────────────

async function fetchAndRender(dashboardId) {
    if (!isConnected) return;
    try {
        const data = await apiFetch(`/api/v1/dashboards/${dashboardId}/data`);
        setConnected(true);
        renderDashboard(data);
        if ($lastUpdated) $lastUpdated.textContent = new Date().toLocaleTimeString();
    } catch (_err) {
        setConnected(false);
        showConnecting();
        scheduleReconnect();
    }
}

function renderDashboard(data) {
    if (!$content) return;
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

    rawData = data;
    renderProcessedTable();
}

function handleSort(colName) {
    if (tableState.sortColumn === colName) {
        tableState.sortDirection = tableState.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        tableState.sortColumn = colName;
        tableState.sortDirection = 'asc';
    }
    tableState.currentPage = 0;
    renderProcessedTable();
}

function handleFilter(text) {
    tableState.filterText = text.toLowerCase();
    tableState.currentPage = 0;
    renderProcessedTable();
}

function handlePageChange(offset) {
    const totalPages = Math.ceil(getFilteredAndSortedRows().length / tableState.pageSize);
    const newPage = tableState.currentPage + offset;
    if (newPage >= 0 && newPage < totalPages) {
        tableState.currentPage = newPage;
        renderProcessedTable();
    }
}

function getFilteredAndSortedRows() {
    let rows = [...rawData.rows];

    if (maxDataValue < 0) maxDataValue = 0;
    rows = rows.slice(0, maxDataValue);

    if (tableState.filterText) {
        rows = rows.filter(row => {
            return rawData.columns.some(col => {
                const cell = row[col];
                if (!cell) return false;
                const searchVal = (cell.display !== undefined && cell.display !== null)
                    ? String(cell.display)
                    : String(cell.value || "");
                return searchVal.toLowerCase().includes(tableState.filterText);
            });
        });
    }

    if (tableState.sortColumn) {
        const col = tableState.sortColumn;
        const dir = tableState.sortDirection === 'asc' ? 1 : -1;
        let isNumeric = true;
        for (const r of rows) {
            const v = (r[col] && r[col].value !== undefined && r[col].value !== null) ? r[col].value : null;
            if (v !== null && isNaN(Number(v))) { isNumeric = false; break; }
        }
        rows.sort((a, b) => {
            let valA = (a[col] && a[col].value !== undefined && a[col].value !== null) ? a[col].value : null;
            let valB = (b[col] && b[col].value !== undefined && b[col].value !== null) ? b[col].value : null;
            if (valA === null && valB === null) return 0;
            if (valA === null) return -1 * dir;
            if (valB === null) return 1 * dir;
            if (isNumeric) return (Number(valA) - Number(valB)) * dir;
            const strA = String(valA).toLowerCase();
            const strB = String(valB).toLowerCase();
            if (strA < strB) return -1 * dir;
            if (strA > strB) return 1 * dir;
            return 0;
        });
    }
    return rows;
}

function renderProcessedTable() {
    if (!$content) return;
    const processedRows = getFilteredAndSortedRows();
    const totalCount = processedRows.length;
    const startIndex = tableState.currentPage * tableState.pageSize;
    const paginatedRows = processedRows.slice(startIndex, startIndex + tableState.pageSize);

    const thead = `<tr>${rawData.columns.map(c => {
        let sortIndicator = "";
        if (tableState.sortColumn === c) {
            sortIndicator = tableState.sortDirection === 'asc' ? " ▴" : " ▾";
        }
        return `<th onclick="handleSort('${esc(c)}')" style="cursor: pointer; user-select: none;">
                  ${esc(c)}<span class="sort-icon">${sortIndicator}</span>
                </th>`;
    }).join("")}</tr>`;

    const allStringValues = new Set();
    rawData.rows.forEach(r => {
        rawData.columns.forEach(c => {
            if (r[c]) {
                const val = (r[c].display !== undefined && r[c].display !== null)
                    ? String(r[c].display)
                    : String(r[c].value || "");
                if (val) allStringValues.add(val);
            }
        });
    });
    const datalistOptions = Array.from(allStringValues).map(v => `<option value="${esc(v)}">`).join("");

    let tbody = paginatedRows.map(row => {
        const cells = rawData.columns.map(col => {
            const cell = row[col] || { value: "", style: "" };
            const rawValue = (cell.value !== undefined && cell.value !== null) ? cell.value : "";
            const displayValue = (cell.display !== undefined && cell.display !== null) ? cell.display : rawValue;
            const styleAttr = cell.style ? ` style="${esc(cell.style)}"` : "";
            const classAttr = (cell.style === "cell-error") ? ` class="cell-error"` : "";
            return `<td${classAttr}${styleAttr} data-value="${esc(String(rawValue))}">${esc(String(displayValue))}</td>`;
        }).join("");
        return `<tr>${cells}</tr>`;
    }).join("");

    if (paginatedRows.length === 0) {
        tbody = `<tr><td colspan="${rawData.columns.length}" style="text-align: center; color: var(--color-text-xs); padding: 30px 10px;">
                    No matching data found for filter: "${esc(tableState.filterText)}" or max items threshold reached.
                 </td></tr>`;
    }

    $content.innerHTML = `
    <div class="dashboard-controls" style="display: flex; gap: 10px; margin-bottom: 12px; align-items: center; flex-wrap: wrap;">
      <input type="text" list="table-filters" class="ui-input" id="tableFilterInput" 
             placeholder="Filter table..." value="${esc(tableState.filterText)}" 
             onkeyup="handleFilter(this.value)" onchange="handleFilter(this.value)"
             style="flex: 1; min-width: 250px;">
      <datalist id="table-filters">${datalistOptions}</datalist>
      <div style="display: flex; gap: 10px; align-items: center; border-left: 1px solid var(--color-border); padding-left: 10px;">
          <input type="number" class="ui-input" id="maxItemsInput" value="${maxDataValue}" 
                 onchange="handleMaxChange(this.value)" placeholder="Max rows" style="width: 100px;" title="Rows cap (set < 0 for empty)">
          <select class="ui-input" id="intervalSelect" onchange="handleIntervalChange(this.value)" style="width: 120px;" title="Refresh Rate">
              <option value="5" ${currentScrapeInterval === 5 ? 'selected' : ''}>5s</option>
              <option value="15" ${currentScrapeInterval === 15 ? 'selected' : ''}>15s</option>
              <option value="30" ${currentScrapeInterval === 30 ? 'selected' : ''}>30s</option>
              <option value="60" ${currentScrapeInterval === 60 ? 'selected' : ''}>60s</option>
              <option value="0" ${currentScrapeInterval === 0 ? 'selected' : ''}>Paused</option>
          </select>
          <button class="nav-btn" style="border: 1px solid var(--color-border); background: var(--color-surface); padding: 8px 12px;" onclick="handleRefresh()">Refresh Now</button>
      </div>
    </div>
    
    <div class="dashboard-card">
      <div class="dashboard-header" style="align-items: center;">
        <span class="dashboard-name">${esc(rawData.dashboard_name || rawData.dashboard_id)}</span>
        <span class="dashboard-meta" style="margin-left: auto;">
          Showing ${startIndex + 1} - ${Math.min(startIndex + tableState.pageSize, totalCount)} of ${totalCount} row(s)
          · refresh ${rawData.scrape_interval_seconds}s
        </span>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>${thead}</thead>
          <tbody>${tbody}</tbody>
        </table>
      </div>
      
      <div class="dashboard-footer" style="padding: 12px 18px; border-top: 1px solid var(--color-border); display: flex; justify-content: space-between; align-items: center; font-size: var(--font-size-xs);">
        <span>Page ${tableState.currentPage + 1} of ${Math.ceil(totalCount / tableState.pageSize) || 1}</span>
        <div style="display: flex; gap: 8px;">
           <button class="nav-btn" style="width: auto; padding: 4px 10px; border: 1px solid var(--color-border);" 
                   onclick="handlePageChange(-1)" ${tableState.currentPage === 0 ? "disabled" : ""}>Previous</button>
           <button class="nav-btn" style="width: auto; padding: 4px 10px; border: 1px solid var(--color-border);" 
                   onclick="handlePageChange(1)" ${(tableState.currentPage + 1) * tableState.pageSize >= totalCount ? "disabled" : ""}>Next</button>
        </div>
      </div>
    </div>`;

    setTimeout(() => {
        const input = document.getElementById("tableFilterInput");
        if (input && document.activeElement !== input) {
            const tempval = input.value;
            input.focus();
            input.value = '';
            input.value = tempval;
        }
    }, 0);
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
initTheme();
checkGitOpsStatus().then(() => {
    // Only start the main app if GitOps is enabled
    if (!$appMainWrapper.classList.contains("hidden")) {
        loadDashboardList();
    }
});
