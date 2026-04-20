/**
 * Chart-Monitor Frontend – Vanilla JS
 *
 * Per-Column Filter Menu (007-column-filter-menu)
 * Polls /api/v1/dashboards for the list, then polls each selected dashboard
 * at its scrape_interval_seconds. All DOM is built with semantic CSS classes
 * defined in styles.css. No utility frameworks required.
 */

const API_BASE = window.location.protocol === "file:" ? "http://localhost:8000" : "";

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
    // filterText REMOVED (007) — global text filter replaced by per-column menus
    currentPage: 0,
    pageSize: 50
};

// ── Column Filter State (007) ─────────────────────────────────────────────────
// _sqlFilterMode REMOVED — replaced by filterMode ('column' | 'sql')
let _sqlResultData = null;   // { columns: string[], rows: RowMap[] } — set on successful SQL run
let columnFilters = {};       // { [colName]: Set<string> } — per-column selected values
let filterMode = 'column';    // 'column' | 'sql' — last-applied-wins
let openMenuColumn = null;    // ephemeral: name of the column whose menu is currently open
let _urlStateRestored = false; // ensure URL state is restored only on first data load

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
const $sqlPanel = document.getElementById("sql-panel");

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
            await loadDashboardList();
        } else {
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

    // Reset all filter state on dashboard switch (T017)
    tableState.sortColumn = null;
    tableState.sortDirection = 'asc';
    tableState.currentPage = 0;
    columnFilters = {};
    filterMode = 'column';
    _sqlResultData = null;
    closeColumnMenu();

    // Clear SQL panel inputs
    const sqlInput = document.getElementById('sql-filter-input');
    if (sqlInput) sqlInput.value = '';
    const sqlError = document.getElementById('sql-filter-error');
    if (sqlError) sqlError.textContent = '';

    syncStateToUrl();
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

function handlePageChange(offset) {
    const totalPages = Math.ceil(getFilteredAndSortedRows().length / tableState.pageSize);
    const newPage = tableState.currentPage + offset;
    if (newPage >= 0 && newPage < totalPages) {
        tableState.currentPage = newPage;
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

    // Restore URL state only on the very first data load (page load / refresh)
    if (!_urlStateRestored) {
        _urlStateRestored = true;
        restoreStateFromUrl();
        return;
    }

    renderProcessedTable();
}

// ── Distinct Values (T004) ────────────────────────────────────────────────────

/**
 * Returns sorted distinct display values for a column from the full rawData.
 * Empty/null cells become the sentinel "(empty)".
 */
function distinctValues(colName) {
    const seen = new Set();
    for (const row of rawData.rows) {
        const cell = row[colName];
        let val;
        if (!cell || (cell.display === null && cell.display === undefined && cell.value === null && cell.value === undefined)) {
            val = '(empty)';
        } else {
            val = (cell.display !== null && cell.display !== undefined)
                ? String(cell.display)
                : String(cell.value !== null && cell.value !== undefined ? cell.value : '');
            if (val === '' || val === 'null') val = '(empty)';
        }
        seen.add(val);
    }
    const result = Array.from(seen);
    result.sort((a, b) => {
        if (a === '(empty)') return 1;
        if (b === '(empty)') return -1;
        return a.toLowerCase().localeCompare(b.toLowerCase());
    });
    return result;
}

// ── Column Menu (T013) ────────────────────────────────────────────────────────

function openColumnMenu(colName, thEl) {
    // Toggle: clicking the same header while open closes the menu
    if (openMenuColumn === colName) {
        closeColumnMenu();
        return;
    }
    closeColumnMenu();

    openMenuColumn = colName;

    const menu = document.getElementById('col-menu');
    if (!menu) return;

    const sortBtn = document.getElementById('col-menu-sort-btn');
    const search = document.getElementById('col-menu-search');
    const valuesList = document.getElementById('col-menu-values');

    // Populate sort button label (T019)
    if (tableState.sortColumn === colName) {
        sortBtn.textContent = tableState.sortDirection === 'asc' ? 'Sort ▴' : 'Sort ▾';
    } else {
        sortBtn.textContent = 'Sort';
    }
    sortBtn.onclick = () => handleColumnSort(colName);

    // Reset search input (T027)
    search.value = '';
    search.oninput = () => filterMenuValues(search.value);

    // Populate value list (T021)
    const values = distinctValues(colName);
    const selectedValues = columnFilters[colName] || new Set();

    if (values.length === 0) {
        valuesList.innerHTML = `<li class="col-menu__empty">No values</li>`;
    } else {
        valuesList.innerHTML = values.map(val => {
            const isChecked = selectedValues.has(val);
            const colJson = esc(JSON.stringify(colName));
            const valJson = esc(JSON.stringify(val));
            return `<li class="col-menu__value-item">
                <label>
                    <input type="checkbox" ${isChecked ? 'checked' : ''}
                        onchange="toggleColumnValue(${colJson}, ${valJson}, this.checked)">
                    ${esc(val)}
                </label>
            </li>`;
        }).join('');
    }

    // Position the menu below the clicked header
    const rect = thEl.getBoundingClientRect();
    menu.style.top = (rect.bottom + 2) + 'px';
    menu.style.left = rect.left + 'px';
    menu.classList.remove('hidden');

    // Outside-click listener — attached after current event finishes (T013)
    const outsideClickHandler = (e) => {
        // Guard: if this menu was already closed and replaced, do nothing
        if (openMenuColumn !== colName) return;
        const m = document.getElementById('col-menu');
        if (!m || m.contains(e.target)) return;
        // Let column header clicks handle their own toggle
        if (e.target.closest && e.target.closest('.col-header')) return;
        closeColumnMenu();
    };
    menu._outsideHandler = outsideClickHandler;
    setTimeout(() => document.addEventListener('click', outsideClickHandler), 0);
}

function closeColumnMenu() {
    const menu = document.getElementById('col-menu');
    if (!menu) return;
    menu.classList.add('hidden');
    if (menu._outsideHandler) {
        document.removeEventListener('click', menu._outsideHandler);
        menu._outsideHandler = null;
    }
    openMenuColumn = null;
}

// ── Sort (T018) ───────────────────────────────────────────────────────────────

function handleColumnSort(colName) {
    if (tableState.sortColumn === colName) {
        tableState.sortDirection = tableState.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        tableState.sortColumn = colName;
        tableState.sortDirection = 'asc';
    }
    tableState.currentPage = 0;

    // Update sort button label in the still-open menu (T019)
    const sortBtn = document.getElementById('col-menu-sort-btn');
    if (sortBtn && openMenuColumn === colName) {
        sortBtn.textContent = tableState.sortDirection === 'asc' ? 'Sort ▴' : 'Sort ▾';
    }

    syncStateToUrl();
    renderProcessedTable();
}

// ── Column Value Filter (T022, T026) ──────────────────────────────────────────

function toggleColumnValue(colName, value, checked) {
    if (checked) {
        if (!columnFilters[colName]) columnFilters[colName] = new Set();
        columnFilters[colName].add(value);
    } else {
        if (columnFilters[colName]) {
            columnFilters[colName].delete(value);
            if (columnFilters[colName].size === 0) delete columnFilters[colName];
        }
    }
    filterMode = 'column';
    tableState.currentPage = 0;
    syncStateToUrl();
    renderProcessedTable();
}

function filterMenuValues(searchText) {
    const valuesList = document.getElementById('col-menu-values');
    if (!valuesList) return;
    const lower = searchText.toLowerCase();
    let anyVisible = false;

    const items = valuesList.querySelectorAll('.col-menu__value-item');
    items.forEach(li => {
        const label = li.querySelector('label');
        const text = label ? label.textContent.trim().toLowerCase() : '';
        const visible = !lower || text.includes(lower);
        li.style.display = visible ? '' : 'none';
        if (visible) anyVisible = true;
    });

    // "No values match" empty state (T028)
    const existingEmpty = valuesList.querySelector('.col-menu__empty--search');
    if (lower && !anyVisible) {
        if (!existingEmpty) {
            const el = document.createElement('li');
            el.className = 'col-menu__empty col-menu__empty--search';
            el.textContent = 'No values match';
            valuesList.appendChild(el);
        }
    } else if (existingEmpty) {
        existingEmpty.remove();
    }
}

// ── URL State Sync (T015, T016) ───────────────────────────────────────────────

function syncStateToUrl() {
    const params = new URLSearchParams();

    if (tableState.sortColumn) {
        params.set('sort', `${encodeURIComponent(tableState.sortColumn)}:${tableState.sortDirection}`);
    }

    for (const [colName, values] of Object.entries(columnFilters)) {
        if (values && values.size > 0) {
            const encoded = Array.from(values).map(v => encodeURIComponent(v)).join(',');
            params.set(`cf_${encodeURIComponent(colName)}`, encoded);
        }
    }

    const sqlInput = document.getElementById('sql-filter-input');
    const sqlText = sqlInput ? sqlInput.value.trim() : '';
    if (sqlText) {
        params.set('sql', sqlText);
    }
    if (filterMode === 'sql' && _sqlResultData) {
        params.set('sql_mode', '1');
    }

    const qs = params.toString();
    history.replaceState(null, '', qs ? `?${qs}` : window.location.pathname);
}

function restoreStateFromUrl() {
    const params = new URLSearchParams(window.location.search);

    // Sort
    const sortParam = params.get('sort');
    if (sortParam) {
        const colonIdx = sortParam.lastIndexOf(':');
        if (colonIdx > 0) {
            tableState.sortColumn = decodeURIComponent(sortParam.substring(0, colonIdx));
            tableState.sortDirection = sortParam.substring(colonIdx + 1) === 'desc' ? 'desc' : 'asc';
        }
    }

    // Column filters
    columnFilters = {};
    for (const [key, val] of params.entries()) {
        if (key.startsWith('cf_')) {
            const colName = decodeURIComponent(key.substring(3));
            const values = val.split(',').map(v => decodeURIComponent(v)).filter(v => v);
            if (values.length > 0) {
                columnFilters[colName] = new Set(values);
            }
        }
    }

    // SQL text
    const sqlText = params.get('sql');
    if (sqlText) {
        const sqlInput = document.getElementById('sql-filter-input');
        if (sqlInput) sqlInput.value = sqlText;
    }

    // Re-execute SQL if sql_mode was active
    if (params.get('sql_mode') === '1' && sqlText) {
        executeSqlFilter(sqlText); // calls renderProcessedTable internally
        return;
    }

    renderProcessedTable();
}

// ── Filter Mode Badge (T033) ──────────────────────────────────────────────────

function activeColumnFilterCount() {
    return Object.keys(columnFilters).filter(k => columnFilters[k] && columnFilters[k].size > 0).length;
}

function hasAnyActiveFilter() {
    return activeColumnFilterCount() > 0
        || !!tableState.sortColumn
        || (filterMode === 'sql' && !!_sqlResultData);
}

function renderFilterModeBadge() {
    if (filterMode === 'sql' && _sqlResultData) {
        return `<span class="filter-mode-badge filter-mode-badge--sql">SQL filter active</span>`;
    }
    const count = activeColumnFilterCount();
    if (count > 0) {
        return `<span class="filter-mode-badge filter-mode-badge--col">Column filters active (${count} column${count > 1 ? 's' : ''})</span>`;
    }
    return `<span class="filter-mode-badge">No active filter</span>`;
}

// ── Clear All Filters (T034) ──────────────────────────────────────────────────

function clearAllFilters() {
    columnFilters = {};
    tableState.sortColumn = null;
    tableState.sortDirection = 'asc';
    tableState.currentPage = 0;
    _sqlResultData = null;
    filterMode = 'column';

    const sqlInput = document.getElementById('sql-filter-input');
    if (sqlInput) sqlInput.value = '';
    const sqlError = document.getElementById('sql-filter-error');
    if (sqlError) sqlError.textContent = '';

    syncStateToUrl();
    renderProcessedTable();
}

// ── Filter & Sort (T005, T006) ────────────────────────────────────────────────

function getFilteredAndSortedRows() {
    // SQL mode: return SQL result rows directly (no client sort/filter/pagination)
    if (filterMode === 'sql' && _sqlResultData) {
        return _sqlResultData.rows;
    }

    let rows = [...rawData.rows];

    if (maxDataValue < 0) maxDataValue = 0;
    rows = rows.slice(0, maxDataValue);

    // Column filters: AND across columns, OR within each column (T025)
    for (const [colName, selectedValues] of Object.entries(columnFilters)) {
        if (!selectedValues || selectedValues.size === 0) continue;
        rows = rows.filter(row => {
            const cell = row[colName];
            let val;
            if (!cell || (cell.display === null && cell.display === undefined && cell.value === null && cell.value === undefined)) {
                val = '(empty)';
            } else {
                val = (cell.display !== null && cell.display !== undefined)
                    ? String(cell.display)
                    : String(cell.value !== null && cell.value !== undefined ? cell.value : '');
                if (val === '' || val === 'null') val = '(empty)';
            }
            return selectedValues.has(val);
        });
    }

    // Sort
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

    const isSqlActive = filterMode === 'sql' && !!_sqlResultData;
    const activeColumns = isSqlActive ? _sqlResultData.columns : rawData.columns;
    const processedRows = getFilteredAndSortedRows();
    const totalCount = processedRows.length;
    const startIndex = isSqlActive ? 0 : tableState.currentPage * tableState.pageSize;
    const paginatedRows = isSqlActive
        ? processedRows
        : processedRows.slice(startIndex, startIndex + tableState.pageSize);

    // Table headers — each th is clickable to open column menu (T014, T020)
    const thead = `<tr>${activeColumns.map(c => {
        let sortIndicator = '';
        if (!isSqlActive && tableState.sortColumn === c) {
            sortIndicator = tableState.sortDirection === 'asc' ? ' ▴' : ' ▾';
        }
        const hasFilter = !isSqlActive && columnFilters[c] && columnFilters[c].size > 0;
        const filteredClass = hasFilter ? ' col-header--filtered' : '';
        const clickHandler = isSqlActive ? '' : `onclick="openColumnMenu(${esc(JSON.stringify(c))}, this)"`;
        return `<th class="col-header${filteredClass}" ${clickHandler}
                    style="cursor: ${isSqlActive ? 'default' : 'pointer'}; user-select: none;">
                  ${esc(c)}<span class="sort-icon">${sortIndicator}</span>
                </th>`;
    }).join('')}</tr>`;

    // Table body
    let tbody = paginatedRows.map(row => {
        const cells = activeColumns.map(col => {
            const cell = row[col] || { value: '', style: '' };
            const rawValue = (cell.value !== undefined && cell.value !== null) ? cell.value : '';
            const displayValue = (cell.display !== undefined && cell.display !== null) ? cell.display : rawValue;
            const styleAttr = cell.style ? ` style="${esc(cell.style)}"` : '';
            const classAttr = (cell.style === 'cell-error') ? ` class="cell-error"` : '';
            return `<td${classAttr}${styleAttr} data-value="${esc(String(rawValue))}">${esc(String(displayValue))}</td>`;
        }).join('');
        return `<tr>${cells}</tr>`;
    }).join('');

    if (paginatedRows.length === 0) {
        const emptyMsg = isSqlActive
            ? 'SQL query returned 0 rows.'
            : `No matching rows${activeColumnFilterCount() > 0 ? ' — column filters active' : ''}.`;
        tbody = `<tr><td colspan="${activeColumns.length}"
                        style="text-align: center; color: var(--color-text-xs); padding: 30px 10px;">
                    ${emptyMsg}
                 </td></tr>`;
    }

    const showStart = totalCount === 0 ? 0 : startIndex + 1;
    const showEnd = Math.min(startIndex + tableState.pageSize, totalCount);

    // Controls bar: badge + clear-all + max-rows + interval + refresh (T010)
    const clearVisible = hasAnyActiveFilter();

    $content.innerHTML = `
    <div class="dashboard-controls" style="display: flex; gap: 10px; margin-bottom: 12px; align-items: center; flex-wrap: wrap;">
      ${renderFilterModeBadge()}
      <button id="clear-all-filters" class="nav-btn"
              style="border: 1px solid var(--color-border); background: var(--color-surface);
                     padding: 4px 10px; width: auto; font-size: var(--font-size-xs);
                     ${clearVisible ? '' : 'display:none;'}"
              onclick="clearAllFilters()">✕ Clear filters</button>
      <div style="display: flex; gap: 10px; align-items: center; margin-left: auto;
                  border-left: 1px solid var(--color-border); padding-left: 10px;">
          <input type="number" class="ui-input" id="maxItemsInput" value="${maxDataValue}"
                 onchange="handleMaxChange(this.value)" placeholder="Max rows"
                 style="width: 100px;" title="Rows cap (set &lt; 0 for empty)">
          <select class="ui-input" id="intervalSelect" onchange="handleIntervalChange(this.value)"
                  style="width: 120px;" title="Refresh Rate">
              <option value="5"  ${currentScrapeInterval === 5  ? 'selected' : ''}>5s</option>
              <option value="15" ${currentScrapeInterval === 15 ? 'selected' : ''}>15s</option>
              <option value="30" ${currentScrapeInterval === 30 ? 'selected' : ''}>30s</option>
              <option value="60" ${currentScrapeInterval === 60 ? 'selected' : ''}>60s</option>
              <option value="0"  ${currentScrapeInterval === 0  ? 'selected' : ''}>Paused</option>
          </select>
          <button class="nav-btn"
                  style="border: 1px solid var(--color-border); background: var(--color-surface); padding: 8px 12px; display:inline-flex; align-items:center; gap:5px;"
                  onclick="handleRefresh()"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>Refresh Now</button>
      </div>
    </div>

    <div class="dashboard-card">
      <div class="dashboard-header" style="align-items: center;">
        <span class="dashboard-name">${esc(rawData.dashboard_name || rawData.dashboard_id)}</span>
        <span class="dashboard-meta" style="margin-left: auto;">
          Showing ${showStart}–${showEnd} of ${totalCount} row(s)
          · refresh ${rawData.scrape_interval_seconds}s
        </span>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>${thead}</thead>
          <tbody>${tbody}</tbody>
        </table>
      </div>

      <div class="dashboard-footer"
           style="padding: 12px 18px; border-top: 1px solid var(--color-border);
                  display: flex; justify-content: space-between; align-items: center;
                  font-size: var(--font-size-xs);">
        <span>${isSqlActive
            ? `SQL: ${totalCount} row(s)`
            : `Page ${tableState.currentPage + 1} of ${Math.ceil(totalCount / tableState.pageSize) || 1}`}</span>
        <div style="display: flex; gap: 8px;">
           <button class="nav-btn"
                   style="width: auto; padding: 4px 10px; border: 1px solid var(--color-border);"
                   onclick="handlePageChange(-1)"
                   ${isSqlActive || tableState.currentPage === 0 ? 'disabled' : ''}>Previous</button>
           <button class="nav-btn"
                   style="width: auto; padding: 4px 10px; border: 1px solid var(--color-border);"
                   onclick="handlePageChange(1)"
                   ${isSqlActive || (tableState.currentPage + 1) * tableState.pageSize >= totalCount ? 'disabled' : ''}>Next</button>
        </div>
      </div>
    </div>`;

    // Show / hide SQL panel (T030)
    if ($sqlPanel) {
        if (window._sqlEngine != null) {
            $sqlPanel.classList.remove('hidden');
        } else {
            $sqlPanel.classList.add('hidden');
        }
    }
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

// ── SQL Filter (T029, T030) ───────────────────────────────────────────────────

/**
 * Build an in-memory sql.js Database from the current rawData.
 * Table is named `data`, columns are rawData.columns (all TEXT).
 */
function buildSqlDatabase() {
    const db = new window._sqlEngine.Database();
    const cols = rawData.columns;
    if (cols.length === 0) return db;
    const colDefs = cols.map(c => `"${c}" TEXT`).join(', ');
    db.run(`CREATE TABLE data (${colDefs})`);
    const placeholders = cols.map(() => '?').join(', ');
    for (const row of rawData.rows) {
        const vals = cols.map(c => {
            const cell = row[c];
            if (!cell) return null;
            const v = cell.value !== undefined && cell.value !== null ? cell.value : null;
            return v !== null ? String(v) : null;
        });
        db.run(`INSERT INTO data VALUES (${placeholders})`, vals);
    }
    return db;
}

/**
 * Execute a SQL query against rawData using sql.js.
 * On success: sets _sqlResultData, sets filterMode='sql', syncs URL, re-renders.
 * On error: shows error message, does NOT change filterMode or _sqlResultData.
 */
function executeSqlFilter(sqlQuery) {
    const errorEl = document.getElementById('sql-filter-error');
    if (!sqlQuery || !sqlQuery.trim()) return;
    if (window._sqlEngine == null) return;

    let db;
    try {
        db = buildSqlDatabase();
        const results = db.exec(sqlQuery.trim());
        if (!results || results.length === 0) {
            _sqlResultData = { columns: rawData.columns, rows: [] };
        } else {
            const { columns, values } = results[0];
            const rows = values.map(vals => {
                const row = {};
                columns.forEach((col, i) => {
                    row[col] = { value: vals[i] !== null ? vals[i] : '', style: '' };
                });
                return row;
            });
            _sqlResultData = { columns, rows };
        }
        filterMode = 'sql';
        if (errorEl) errorEl.textContent = '';
        syncStateToUrl();
        renderProcessedTable();
    } catch (err) {
        if (errorEl) errorEl.textContent = String(err);
        _sqlResultData = null;
    } finally {
        if (db) db.close();
    }
}

// ── Boot ──────────────────────────────────────────────────────────────────────

window._sqlEngine = null;
if (typeof initSqlJs === 'function') {
    initSqlJs({ locateFile: f => `./assets/${f}` })
        .then(SQL => {
            window._sqlEngine = SQL;
            // Wire Run SQL button now that the engine is ready
            const runBtn = document.getElementById('sql-run-btn');
            if (runBtn) {
                runBtn.onclick = () => {
                    const input = document.getElementById('sql-filter-input');
                    if (input) executeSqlFilter(input.value);
                };
            }
            // Show SQL panel if a dashboard is already displayed
            if ($sqlPanel && currentDashboardId) {
                $sqlPanel.classList.remove('hidden');
            }
        })
        .catch(() => { window._sqlEngine = null; });
}

// Wire SQL textarea Enter key (Shift+Enter = newline)
const $sqlInput = document.getElementById('sql-filter-input');
if ($sqlInput) {
    $sqlInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            executeSqlFilter($sqlInput.value);
        }
    });
}

initTheme();
checkGitOpsStatus().then(() => {
    if (!$appMainWrapper.classList.contains("hidden")) {
        loadDashboardList();
    }
});
