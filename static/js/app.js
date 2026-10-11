/**
 * Automated File Organizer Pro - Full-Stack Client Application
 */

// Global State Store
const state = {
    currentPath: '',
    scannedData: null,
    previewData: null,
    selectedFiles: new Set(),
    activeTab: 'tab-organizer',
    charts: {
        category: null,
        count: null
    },
    logTimer: null
};

// DOM Elements Cache
const elements = {
    // Nav & Theme
    navButtons: document.querySelectorAll('.nav-item'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    pageTitle: document.getElementById('page-title'),
    pageSubtitle: document.getElementById('page-subtitle'),
    themeToggle: document.getElementById('theme-toggle'),
    btnCreateSandbox: document.getElementById('btn-create-sandbox'),
    btnEmptySandbox: document.getElementById('btn-empty-sandbox'),

    // Inputs & Filters
    targetFolderInput: document.getElementById('target-folder-input'),
    shortcutsBar: document.getElementById('shortcuts-bar'),
    btnOpenExplorer: document.getElementById('btn-open-explorer'),
    btnScanFolder: document.getElementById('btn-scan-folder'),
    strategySelect: document.getElementById('strategy-select'),
    optDuplicates: document.getElementById('opt-duplicates'),
    optCustomRules: document.getElementById('opt-custom-rules'),
    optCleanEmpty: document.getElementById('opt-clean-empty'),
    optRecursive: document.getElementById('opt-recursive'),

    // Stats & Categories
    statsContainer: document.getElementById('stats-container'),
    statTotalFiles: document.getElementById('stat-total-files'),
    statTotalSize: document.getElementById('stat-total-size'),
    statDuplicateCount: document.getElementById('stat-duplicate-count'),
    statWastedSpace: document.getElementById('stat-wasted-space'),
    statCategoryCount: document.getElementById('stat-category-count'),
    statScanTime: document.getElementById('stat-scan-time'),
    categoriesBar: document.getElementById('categories-bar'),
    categoryChips: document.getElementById('category-chips'),

    // Files View
    filesSection: document.getElementById('files-section'),
    emptyStateBanner: document.getElementById('empty-state-banner'),
    subTabBtns: document.querySelectorAll('.sub-tab-btn'),
    subTabContents: document.querySelectorAll('.subtab-content'),
    tabCountAll: document.getElementById('tab-count-all'),
    tabCountDup: document.getElementById('tab-count-dup'),
    fileSearchFilter: document.getElementById('file-search-filter'),
    selectAllFiles: document.getElementById('select-all-files'),
    filesTableBody: document.getElementById('files-table-body'),
    duplicatesGroupContainer: document.getElementById('duplicates-group-container'),
    btnPreviewDryrun: document.getElementById('btn-preview-dryrun'),
    btnExecuteOrganize: document.getElementById('btn-execute-organize'),

    // Watcher
    watcherFolderInput: document.getElementById('watcher-folder-input'),
    watcherStrategySelect: document.getElementById('watcher-strategy-select'),
    btnStartWatcher: document.getElementById('btn-start-watcher'),
    btnRefreshWatchers: document.getElementById('btn-refresh-watchers'),
    watchersList: document.getElementById('watchers-list'),
    watcherBadgeDot: document.getElementById('watcher-badge-dot'),
    watcherHeroStatus: document.getElementById('watcher-hero-status'),
    watcherHeroText: document.getElementById('watcher-hero-text'),

    // History
    historyBatchesContainer: document.getElementById('history-batches-container'),
    btnRefreshHistory: document.getElementById('btn-refresh-history'),

    // Rules
    formCreateRule: document.getElementById('form-create-rule'),
    customRulesContainer: document.getElementById('custom-rules-container'),
    categoriesRefContainer: document.getElementById('categories-ref-container'),

    // Logs
    terminalBody: document.getElementById('terminal-body'),
    btnRefreshLogs: document.getElementById('btn-refresh-logs'),
    btnClearLogsView: document.getElementById('btn-clear-logs-view'),

    // Modals
    previewModal: document.getElementById('preview-modal'),
    modalClose: document.getElementById('modal-close'),
    btnModalCancel: document.getElementById('btn-modal-cancel'),
    btnModalConfirmExecute: document.getElementById('btn-modal-confirm-execute'),
    modalContentBody: document.getElementById('modal-content-body'),
    batchDetailsModal: document.getElementById('batch-details-modal'),
    batchModalClose: document.getElementById('batch-modal-close'),
    btnBatchModalClose: document.getElementById('btn-batch-modal-close'),
    batchModalBody: document.getElementById('batch-modal-body'),
    toastContainer: document.getElementById('toast-container')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavigation();
    initShortcuts();
    initCustomRules();
    initCategoriesReference();
    initWatchers();
    initHistory();
    initEventListeners();
    startLogStream();
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('autofile_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    elements.themeToggle.checked = savedTheme === 'dark';

    elements.themeToggle.addEventListener('change', (e) => {
        const theme = e.target.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('autofile_theme', theme);
        renderCharts();
    });
}

// Navigation Tabs
function initNavigation() {
    const tabHeaders = {
        'tab-organizer': { title: 'Organizer Studio', subtitle: 'Scan, categorize, detect duplicates and automate file organization with atomic undo.' },
        'tab-watcher': { title: 'Auto-Pilot Live Watcher', subtitle: 'Continuous background directory monitor that organizes new incoming files automatically.' },
        'tab-history': { title: 'History & 1-Click Rollback', subtitle: 'Complete audit log of all organization batches with instant reversible undo operations.' },
        'tab-rules': { title: 'Smart Custom Rules Engine', subtitle: 'Define granular pattern, prefix, extension and regex rules with customizable subfolder routing.' },
        'tab-analytics': { title: 'Storage & Breakdown Insights', subtitle: 'Visual analytics, category proportions, and duplicate space recovery metrics.' },
        'tab-logs': { title: 'Live Activity Terminal', subtitle: 'Real-time operational event stream, error diagnostics, and system auditing.' }
    };

    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            elements.navButtons.forEach(b => b.classList.remove('active'));
            elements.tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(targetTab)?.classList.add('active');
            state.activeTab = targetTab;

            if (tabHeaders[targetTab]) {
                elements.pageTitle.textContent = tabHeaders[targetTab].title;
                elements.pageSubtitle.textContent = tabHeaders[targetTab].subtitle;
            }

            if (targetTab === 'tab-analytics') {
                renderCharts();
            } else if (targetTab === 'tab-history') {
                fetchHistory();
            } else if (targetTab === 'tab-watcher') {
                fetchWatchers();
            } else if (targetTab === 'tab-logs') {
                fetchLogs();
            }
        });
    });

    // Sub Tabs inside Studio
    elements.subTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-subtab');
            elements.subTabBtns.forEach(b => b.classList.remove('active'));
            elements.subTabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`subtab-${target}`)?.classList.add('active');
        });
    });
}

// Directory Shortcuts
async function initShortcuts() {
    try {
        const res = await fetch('/api/shortcuts');
        const data = await res.json();
        if (data.shortcuts && data.shortcuts.length) {
            elements.shortcutsBar.innerHTML = '';
            data.shortcuts.forEach(s => {
                const chip = document.createElement('button');
                chip.className = 'shortcut-chip';
                chip.innerHTML = `<i class="fa-solid ${s.icon}"></i> ${s.name}`;
                chip.addEventListener('click', () => {
                    elements.targetFolderInput.value = s.path;
                    scanCurrentDirectory();
                });
                elements.shortcutsBar.appendChild(chip);
            });

            if (data.default_path && !elements.targetFolderInput.value) {
                elements.targetFolderInput.value = data.default_path;
            }
        }
    } catch (err) {
        console.error('Error fetching shortcuts:', err);
    }
}

// Scan Directory
async function scanCurrentDirectory() {
    const folderPath = elements.targetFolderInput.value.trim();
    if (!folderPath) {
        showToast('Please enter or select a directory path.', 'error');
        return;
    }

    elements.btnScanFolder.disabled = true;
    elements.btnScanFolder.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: folderPath,
                strategy: elements.strategySelect.value,
                recursive: elements.optRecursive.checked,
                detect_duplicates: elements.optDuplicates.checked,
                quarantine_duplicates: elements.optDuplicates.checked,
                use_custom_rules: elements.optCustomRules.checked
            })
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            showToast(result.error || 'Failed to scan directory', 'error');
            return;
        }

        state.scannedData = result.data;
        state.currentPath = result.data.root_dir;
        state.selectedFiles.clear();

        // Select all files by default
        result.data.files.forEach(f => state.selectedFiles.add(f.path));

        renderScanResults(result.data);
        showToast(`Scanned ${result.data.total_files} files successfully!`, 'success');

        // Update charts if in background
        renderCharts();

    } catch (err) {
        showToast('Connection error scanning directory: ' + err.message, 'error');
    } finally {
        elements.btnScanFolder.disabled = false;
        elements.btnScanFolder.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> <span>Scan Directory</span>';
    }
}

// Render Scan Results
function renderScanResults(data) {
    // Show sections
    elements.emptyStateBanner.style.display = 'none';
    elements.statsContainer.style.display = 'grid';
    elements.categoriesBar.style.display = 'block';
    elements.filesSection.style.display = 'block';

    // Populate Stats
    elements.statTotalFiles.textContent = data.total_files;
    elements.statTotalSize.textContent = data.total_size_formatted;
    elements.statDuplicateCount.textContent = data.duplicates_count;
    elements.statWastedSpace.textContent = `${data.wasted_duplicate_formatted} duplicate`;
    elements.statCategoryCount.textContent = data.categories.length;
    elements.statScanTime.textContent = `Scan time: ${data.scan_duration_sec}s`;

    // Populate Category Chips
    elements.categoryChips.innerHTML = '';
    data.categories.forEach(cat => {
        const chip = document.createElement('div');
        chip.className = 'category-chip-item';
        chip.style.backgroundColor = cat.bg_color;
        chip.style.borderColor = cat.color;
        chip.style.color = cat.color;
        chip.innerHTML = `<i class="fa-solid ${cat.icon}"></i> <span>${cat.name}</span> <strong>(${cat.count})</strong>`;
        elements.categoryChips.appendChild(chip);
    });

    // Counts on Sub Tabs
    elements.tabCountAll.textContent = data.total_files;
    elements.tabCountDup.textContent = data.duplicate_groups.length;

    // Render Table Rows
    renderFilesTable(data.files);

    // Render Duplicates Tab
    renderDuplicatesGroups(data.duplicate_groups);
}

// Render Files Table with Filter
function renderFilesTable(files) {
    const filterText = elements.fileSearchFilter.value.toLowerCase().trim();
    const filtered = files.filter(f => 
        !filterText || 
        f.name.toLowerCase().includes(filterText) || 
        f.category.toLowerCase().includes(filterText) ||
        f.extension.toLowerCase().includes(filterText)
    );

    elements.filesTableBody.innerHTML = '';

    if (filtered.length === 0) {
        elements.filesTableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    <i class="fa-solid fa-filter-circle-xmark" style="font-size: 1.5rem; margin-bottom: 0.5rem; display: block;"></i>
                    No files matching your search filter
                </td>
            </tr>
        `;
        return;
    }

    filtered.forEach(file => {
        const tr = document.createElement('tr');
        const isChecked = state.selectedFiles.has(file.path);

        tr.innerHTML = `
            <td>
                <input type="checkbox" class="file-row-checkbox" data-path="${file.path}" ${isChecked ? 'checked' : ''}>
            </td>
            <td>
                <div class="file-cell">
                    <div class="file-icon-box" style="background-color: ${file.bg_color}; color: ${file.color};">
                        <i class="fa-solid ${file.icon}"></i>
                    </div>
                    <span>${file.name}</span>
                    ${file.is_duplicate ? '<span class="badge-duplicate">DUPLICATE</span>' : ''}
                </div>
            </td>
            <td>
                <span class="category-tag" style="background-color: ${file.bg_color}; color: ${file.color};">
                    <i class="fa-solid ${file.icon}"></i> ${file.display_category || file.category}
                </span>
            </td>
            <td>${file.size_formatted}</td>
            <td style="color: var(--text-muted); font-size: 0.8rem;">${file.modified_formatted}</td>
            <td>
                <span class="destination-tag">
                    <i class="fa-solid fa-folder-tree"></i> ${file.target_subfolder}
                </span>
            </td>
        `;

        // Checkbox event
        const chk = tr.querySelector('.file-row-checkbox');
        chk.addEventListener('change', (e) => {
            if (e.target.checked) {
                state.selectedFiles.add(file.path);
            } else {
                state.selectedFiles.delete(file.path);
            }
            updateSelectAllState();
        });

        elements.filesTableBody.appendChild(tr);
    });

    updateSelectAllState();
}

function updateSelectAllState() {
    if (!state.scannedData || !state.scannedData.files.length) return;
    elements.selectAllFiles.checked = state.selectedFiles.size === state.scannedData.files.length;
}

// Render Duplicates Groups
function renderDuplicatesGroups(groups) {
    elements.duplicatesGroupContainer.innerHTML = '';
    if (!groups || groups.length === 0) {
        elements.duplicatesGroupContainer.innerHTML = `
            <div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
                <i class="fa-solid fa-circle-check" style="font-size: 2.5rem; color: var(--success); margin-bottom: 0.75rem; display: block;"></i>
                <h4>No Duplicates Found!</h4>
                <p>All files in this directory have unique content hashes.</p>
            </div>
        `;
        return;
    }

    groups.forEach((grp, idx) => {
        const card = document.createElement('div');
        card.className = 'dup-group-card';
        card.innerHTML = `
            <div class="dup-group-header">
                <div>
                    <strong><i class="fa-solid fa-clone text-primary"></i> Duplicate Group #${idx + 1}: ${grp.file_name}</strong>
                    <span style="color: var(--text-muted); margin-left: 0.5rem;">(${grp.count} identical copies, ${grp.size_formatted} each)</span>
                </div>
                <div class="dup-hash-tag">SHA-256: ${grp.hash.substring(0, 16)}...</div>
            </div>
            <div class="dup-files-list">
                ${grp.files.map((f, fidx) => `
                    <div class="dup-file-row">
                        <div style="display: flex; align-items: center; gap: 0.6rem;">
                            <i class="fa-solid ${f.icon}" style="color: ${f.color}"></i>
                            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;">${f.path}</span>
                        </div>
                        <div>
                            ${fidx === 0 ? '<span class="badge-original">ORIGINAL (Keep)</span>' : '<span class="badge-duplicate">DUPLICATE (Move)</span>'}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        elements.duplicatesGroupContainer.appendChild(card);
    });
}

// Dry Run Preview
async function runDryRunPreview() {
    const folderPath = elements.targetFolderInput.value.trim();
    if (!folderPath) {
        showToast('Please specify a directory first.', 'error');
        return;
    }

    elements.btnPreviewDryrun.disabled = true;
    elements.btnPreviewDryrun.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Simulating...';

    try {
        const response = await fetch('/api/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: folderPath,
                strategy: elements.strategySelect.value,
                recursive: elements.optRecursive.checked,
                detect_duplicates: elements.optDuplicates.checked,
                quarantine_duplicates: elements.optDuplicates.checked,
                use_custom_rules: elements.optCustomRules.checked
            })
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            showToast(result.error || 'Preview failed', 'error');
            return;
        }

        state.previewData = result.data;
        showPreviewModal(result.data);

    } catch (err) {
        showToast('Preview error: ' + err.message, 'error');
    } finally {
        elements.btnPreviewDryrun.disabled = false;
        elements.btnPreviewDryrun.innerHTML = '<i class="fa-solid fa-eye"></i> <span>Dry Run Preview</span>';
    }
}

// Show Preview Modal
function showPreviewModal(data) {
    const moves = data.planned_moves;
    const toMoveCount = moves.filter(m => !m.is_already_in_place).length;
    const unchangedCount = moves.filter(m => m.is_already_in_place).length;

    elements.modalContentBody.innerHTML = `
        <div style="margin-bottom: 1.5rem; display: flex; gap: 1rem; flex-wrap: wrap;">
            <div class="stat-card glass-card" style="flex: 1; padding: 1rem;">
                <span class="stat-label">Action Target</span>
                <strong style="font-family: 'JetBrains Mono'; font-size: 0.85rem; word-break: break-all;">${data.root_dir}</strong>
            </div>
            <div class="stat-card glass-card" style="flex: 1; padding: 1rem;">
                <span class="stat-label">Strategy</span>
                <strong style="color: var(--primary);">${data.strategy.toUpperCase()}</strong>
            </div>
            <div class="stat-card glass-card" style="flex: 1; padding: 1rem;">
                <span class="stat-label">Moves Planned</span>
                <strong style="color: var(--success);">${toMoveCount} files</strong> <span style="color: var(--text-muted); font-size: 0.75rem;">(${unchangedCount} already sorted)</span>
            </div>
        </div>

        <h4 style="margin-bottom: 0.75rem; font-size: 0.95rem;"><i class="fa-solid fa-arrow-right-arrow-left text-primary"></i> Planned File Relocations:</h4>
        <div class="table-responsive" style="max-height: 380px;">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Category</th>
                        <th>Target Subfolder</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${moves.map(m => `
                        <tr>
                            <td>
                                <div class="file-cell">
                                    <i class="fa-solid ${m.icon}" style="color: ${m.color}"></i>
                                    <span>${m.file_name}</span>
                                </div>
                            </td>
                            <td><span class="category-tag" style="background-color: ${m.bg_color}; color: ${m.color};">${m.category}</span></td>
                            <td><span class="destination-tag">${m.target_subfolder}</span></td>
                            <td>
                                ${m.is_already_in_place 
                                    ? '<span style="color: var(--text-muted); font-size: 0.75rem;"><i class="fa-solid fa-check"></i> Already in place</span>' 
                                    : '<span style="color: var(--success); font-weight: 700; font-size: 0.75rem;"><i class="fa-solid fa-arrow-right"></i> Will Move</span>'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    elements.previewModal.classList.add('active');
}

// Execute Live Organization
async function executeOrganization() {
    const folderPath = elements.targetFolderInput.value.trim();
    if (!folderPath) {
        showToast('Please specify a directory first.', 'error');
        return;
    }

    elements.btnExecuteOrganize.disabled = true;
    elements.btnExecuteOrganize.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Organizing...';

    const selectedList = state.selectedFiles.size > 0 ? Array.from(state.selectedFiles) : null;

    try {
        const response = await fetch('/api/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: folderPath,
                strategy: elements.strategySelect.value,
                recursive: elements.optRecursive.checked,
                detect_duplicates: elements.optDuplicates.checked,
                quarantine_duplicates: elements.optDuplicates.checked,
                use_custom_rules: elements.optCustomRules.checked,
                clean_empty_folders: elements.optCleanEmpty.checked,
                selected_files: selectedList
            })
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            showToast(result.error || 'Failed to organize files', 'error');
            return;
        }

        elements.previewModal.classList.remove('active');
        showToast(`🎉 Success! Moved ${result.summary.moved_files} files into structured folders.`, 'success');

        // Re-scan directory to refresh view
        await scanCurrentDirectory();
        fetchHistory();

    } catch (err) {
        showToast('Execution error: ' + err.message, 'error');
    } finally {
        elements.btnExecuteOrganize.disabled = false;
        elements.btnExecuteOrganize.innerHTML = '<i class="fa-solid fa-bolt"></i> <span>Execute Organization</span>';
    }
}

// Auto-Pilot Watchers
async function fetchWatchers() {
    try {
        const res = await fetch('/api/watchers');
        const data = await res.json();
        if (!data.success) return;

        const watchers = data.watchers;
        const anyActive = watchers.some(w => w.is_active);

        // Update badge indicator
        if (anyActive) {
            elements.watcherBadgeDot.style.display = 'block';
            elements.watcherHeroStatus.className = 'status-badge-large';
            elements.watcherHeroText.textContent = `${watchers.filter(w => w.is_active).length} Watcher(s) Active & Monitoring`;
        } else {
            elements.watcherBadgeDot.style.display = 'none';
            elements.watcherHeroStatus.className = 'status-badge-large';
            elements.watcherHeroText.textContent = 'No Watchers Active';
        }

        elements.watchersList.innerHTML = '';
        if (watchers.length === 0) {
            elements.watchersList.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-muted);">
                    <i class="fa-solid fa-satellite-dish" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                    No folder watchers configured. Add your Downloads or Desktop folder above.
                </div>
            `;
            return;
        }

        watchers.forEach(w => {
            const card = document.createElement('div');
            card.className = 'watcher-card';
            card.innerHTML = `
                <div class="watcher-card-header">
                    <span class="status-badge-large" style="margin: 0; padding: 2px 10px; font-size: 0.72rem; ${w.is_active ? '' : 'background: rgba(100,116,139,0.15); color: #94a3b8; border-color: rgba(100,116,139,0.3);'}">
                        <span class="pulse-dot" style="${w.is_active ? '' : 'background: #64748b; box-shadow: none; animation: none;'}"></span>
                        ${w.is_active ? 'MONITORING' : 'STOPPED'}
                    </span>
                    <button class="btn btn-danger btn-sm" onclick="deleteWatcherConfig(${w.id})">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
                <div class="watcher-path"><i class="fa-solid fa-folder text-primary"></i> ${w.folder_path}</div>
                <div style="display: flex; gap: 0.5rem; font-size: 0.8rem; color: var(--text-secondary);">
                    <span>Strategy: <strong>${w.strategy}</strong></span>
                </div>
                <div class="watcher-feed">
                    ${w.recent_events && w.recent_events.length > 0 
                        ? w.recent_events.map(ev => `<div>[${ev.timestamp}] ${ev.status}: ${ev.file}</div>`).join('') 
                        : '<div style="color: var(--text-muted);">No new files detected yet. Waiting for incoming downloads...</div>'}
                </div>
                <div>
                    ${w.is_active 
                        ? `<button class="btn btn-secondary btn-sm btn-block" onclick="stopWatcherFolder('${escapeJs(w.folder_path)}')"><i class="fa-solid fa-stop"></i> Pause Monitoring</button>`
                        : `<button class="btn btn-primary btn-sm btn-block" onclick="startWatcherFolder('${escapeJs(w.folder_path)}', '${w.strategy}')"><i class="fa-solid fa-play"></i> Resume Monitoring</button>`}
                </div>
            `;
            elements.watchersList.appendChild(card);
        });

    } catch (err) {
        console.error('Error fetching watchers:', err);
    }
}

async function startWatcherFolder(folderPath, strategy = 'category') {
    try {
        const res = await fetch('/api/watchers/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath, strategy: strategy })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            fetchWatchers();
        } else {
            showToast(data.error || 'Failed to start watcher', 'error');
        }
    } catch (err) {
        showToast('Error starting watcher: ' + err.message, 'error');
    }
}

async function stopWatcherFolder(folderPath) {
    try {
        const res = await fetch('/api/watchers/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'info');
            fetchWatchers();
        }
    } catch (err) {
        showToast('Error stopping watcher: ' + err.message, 'error');
    }
}

window.deleteWatcherConfig = async function(id) {
    if (!confirm('Are you sure you want to delete this watcher?')) return;
    try {
        const res = await fetch(`/api/watchers/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast('Watcher removed', 'info');
            fetchWatchers();
        }
    } catch (err) {
        showToast('Error deleting watcher: ' + err.message, 'error');
    }
};

window.startWatcherFolder = startWatcherFolder;
window.stopWatcherFolder = stopWatcherFolder;

// Organization History & Rollback
async function fetchHistory() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        if (!data.success) return;

        elements.historyBatchesContainer.innerHTML = '';
        if (data.batches.length === 0) {
            elements.historyBatchesContainer.innerHTML = `
                <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                    <i class="fa-solid fa-clock-rotate-left" style="font-size: 2.5rem; margin-bottom: 0.75rem; display: block;"></i>
                    <h4>No Organization History Yet</h4>
                    <p>Once you run an organization batch, it will be saved here with 1-click rollback support.</p>
                </div>
            `;
            return;
        }

        data.batches.forEach(b => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="history-meta">
                    <div class="history-title">
                        <span>Batch ID: <strong style="font-family: 'JetBrains Mono';">${b.batch_id}</strong></span>
                        ${b.is_rolled_back 
                            ? '<span class="badge-tag" style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3);"><i class="fa-solid fa-rotate-left"></i> ROLLED BACK</span>'
                            : '<span class="badge-tag" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3);"><i class="fa-solid fa-check"></i> ACTIVE</span>'}
                    </div>
                    <div class="history-sub">
                        <i class="fa-solid fa-folder"></i> ${b.root_dir} &bull; Strategy: <strong>${b.strategy}</strong> &bull; Moved: <strong>${b.moved_files}</strong> files &bull; ${b.created_at}
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn btn-secondary btn-sm" onclick="viewBatchDetails('${b.batch_id}')">
                        <i class="fa-solid fa-eye"></i> View Files
                    </button>
                    ${!b.is_rolled_back ? `
                        <button class="btn btn-danger btn-sm" onclick="executeRollback('${b.batch_id}')">
                            <i class="fa-solid fa-rotate-left"></i> Rollback Batch
                        </button>
                    ` : ''}
                </div>
            `;
            elements.historyBatchesContainer.appendChild(item);
        });

    } catch (err) {
        console.error('Error fetching history:', err);
    }
}

window.viewBatchDetails = async function(batchId) {
    try {
        const res = await fetch(`/api/history/${batchId}`);
        const data = await res.json();
        if (!data.success) return;

        elements.batchModalTitle.textContent = `Operations for Batch ${batchId}`;
        elements.batchModalBody.innerHTML = `
            <div class="table-responsive" style="max-height: 400px;">
                <table class="modern-table">
                    <thead>
                        <tr>
                            <th>Original Path</th>
                            <th>New Location</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.operations.map(op => `
                            <tr>
                                <td style="font-family: 'JetBrains Mono'; font-size: 0.8rem;">${op.original_path}</td>
                                <td style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--primary);">${op.new_path}</td>
                                <td>
                                    <span class="badge-tag" style="${op.status === 'rolled_back' ? 'background: rgba(239,68,68,0.15); color: #ef4444;' : 'background: rgba(16,185,129,0.15); color: #10b981;'}">
                                        ${op.status.toUpperCase()}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        elements.batchDetailsModal.classList.add('active');
    } catch (err) {
        showToast('Failed to load batch details', 'error');
    }
};

window.executeRollback = async function(batchId) {
    if (!confirm(`Are you sure you want to rollback all files in Batch ${batchId}? Every file will be moved back to its original location.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/history/${batchId}/rollback`, { method: 'POST' });
        const result = await res.json();
        if (result.success) {
            showToast(`Batch ${batchId} rolled back successfully! Restored ${result.restored_files} files.`, 'success');
            fetchHistory();
            if (state.currentPath) {
                scanCurrentDirectory();
            }
        } else {
            showToast(result.error || 'Rollback failed', 'error');
        }
    } catch (err) {
        showToast('Rollback error: ' + err.message, 'error');
    }
};

// Custom Rules Engine
async function initCustomRules() {
    try {
        const res = await fetch('/api/rules');
        const data = await res.json();
        if (!data.success) return;

        elements.customRulesContainer.innerHTML = '';
        if (data.rules.length === 0) {
            elements.customRulesContainer.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    <i class="fa-solid fa-sliders" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                    No custom rules created yet. Add one using the form on the left!
                </div>
            `;
            return;
        }

        data.rules.forEach(rule => {
            const card = document.createElement('div');
            card.className = 'rule-card';
            card.innerHTML = `
                <div>
                    <div style="font-weight: 700; margin-bottom: 0.25rem;">
                        <i class="fa-solid fa-filter text-primary"></i> ${rule.name}
                        <span class="badge-tag" style="margin-left: 0.5rem;">Priority ${rule.priority}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">
                        Condition: <strong>${rule.condition_type}</strong> ("${rule.pattern}") &rarr; Target: <strong style="color: var(--accent-cyan);">${rule.target_folder}</strong>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <label class="switch">
                        <input type="checkbox" ${rule.enabled ? 'checked' : ''} onchange="toggleCustomRule(${rule.id}, this.checked)">
                        <span class="slider round"></span>
                    </label>
                    <button class="btn btn-danger btn-sm" onclick="deleteCustomRuleById(${rule.id})">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            `;
            elements.customRulesContainer.appendChild(card);
        });

    } catch (err) {
        console.error('Error fetching custom rules:', err);
    }
}

window.toggleCustomRule = async function(id, enabled) {
    try {
        await fetch(`/api/rules/${id}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: enabled })
        });
        showToast('Rule status updated', 'info');
    } catch (err) {
        showToast('Failed to toggle rule', 'error');
    }
};

window.deleteCustomRuleById = async function(id) {
    if (!confirm('Delete this rule?')) return;
    try {
        const res = await fetch(`/api/rules/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast('Rule deleted', 'info');
            initCustomRules();
        }
    } catch (err) {
        showToast('Error deleting rule', 'error');
    }
};

// Built-in Categories Cheatsheet
async function initCategoriesReference() {
    try {
        const res = await fetch('/api/categories');
        const data = await res.json();
        if (!data.success) return;

        elements.categoriesRefContainer.innerHTML = '';
        data.order.forEach(catName => {
            const meta = data.metadata[catName] || {};
            const exts = data.categories[catName] || [];

            const card = document.createElement('div');
            card.className = 'cat-ref-card';
            card.innerHTML = `
                <div class="cat-ref-header" style="color: ${meta.color || 'var(--text-primary)'};">
                    <i class="fa-solid ${meta.icon || 'fa-file'}"></i>
                    <span>${catName}</span>
                </div>
                <div class="ext-badge-list">
                    ${exts.map(e => `<span class="ext-badge">${e}</span>`).join('')}
                </div>
            `;
            elements.categoriesRefContainer.appendChild(card);
        });

    } catch (err) {
        console.error('Error loading category metadata:', err);
    }
}

// Storage Insights Charts (Chart.js)
function renderCharts() {
    if (!state.scannedData) return;

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#f8fafc' : '#0f172a';
    const categories = state.scannedData.categories;

    const labels = categories.map(c => c.name);
    const sizeData = categories.map(c => (c.size_bytes / (1024 * 1024)).toFixed(2)); // MB
    const countData = categories.map(c => c.count);
    const colors = categories.map(c => c.color || '#6366f1');

    // 1. Doughnut Chart for Size
    const ctxCategory = document.getElementById('category-chart');
    if (ctxCategory) {
        if (state.charts.category) state.charts.category.destroy();
        state.charts.category = new Chart(ctxCategory, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: sizeData,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: isDark ? '#1e293b' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } } },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ` ${ctx.label}: ${ctx.raw} MB`;
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Bar Chart for File Counts
    const ctxCount = document.getElementById('count-chart');
    if (ctxCount) {
        if (state.charts.count) state.charts.count.destroy();
        state.charts.count = new Chart(ctxCount, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Files',
                    data: countData,
                    backgroundColor: colors,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: textColor } },
                    y: { ticks: { color: textColor }, grid: { color: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// Live Logs Stream
async function fetchLogs() {
    try {
        const res = await fetch('/api/logs?lines=60');
        const data = await res.json();
        if (!data.success) return;

        elements.terminalBody.innerHTML = '';
        if (data.logs.length === 0) {
            elements.terminalBody.innerHTML = '<div style="color: var(--text-muted);">No system events logged yet.</div>';
            return;
        }

        data.logs.forEach(line => {
            const div = document.createElement('div');
            div.className = 'log-line';

            let className = 'log-info';
            if (line.includes('ERROR') || line.includes('Failed')) className = 'log-error';
            else if (line.includes('WARNING')) className = 'log-warn';

            div.innerHTML = `<span class="${className}">${escapeHtml(line)}</span>`;
            elements.terminalBody.appendChild(div);
        });

        elements.terminalBody.scrollTop = elements.terminalBody.scrollHeight;
    } catch (err) {
        console.error('Error fetching logs:', err);
    }
}

function startLogStream() {
    state.logTimer = setInterval(() => {
        if (state.activeTab === 'tab-logs') {
            fetchLogs();
        }
    }, 3000);
}

// Event Listeners
function initEventListeners() {
    // Scan button
    elements.btnScanFolder.addEventListener('click', scanCurrentDirectory);

    // Enter key on folder input
    elements.targetFolderInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') scanCurrentDirectory();
    });

    // Strategy select change re-scans/re-evaluates
    elements.strategySelect.addEventListener('change', () => {
        if (elements.targetFolderInput.value.trim()) {
            scanCurrentDirectory();
        }
    });

    // Checkboxes change re-evaluates
    [elements.optDuplicates, elements.optCustomRules, elements.optRecursive].forEach(el => {
        el.addEventListener('change', () => {
            if (elements.targetFolderInput.value.trim()) {
                scanCurrentDirectory();
            }
        });
    });

    // Open in Windows Explorer
    elements.btnOpenExplorer.addEventListener('click', async () => {
        const folder = elements.targetFolderInput.value.trim();
        if (!folder) return;
        try {
            const res = await fetch('/api/open-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: folder })
            });
            const data = await res.json();
            if (data.success) {
                showToast(data.message, 'info');
            } else {
                showToast(data.error || 'Could not open explorer', 'error');
            }
        } catch (err) {
            showToast('Error opening explorer', 'error');
        }
    });

    // File Search Filter
    elements.fileSearchFilter.addEventListener('input', () => {
        if (state.scannedData) {
            renderFilesTable(state.scannedData.files);
        }
    });

    // Select All Checkbox
    elements.selectAllFiles.addEventListener('change', (e) => {
        if (!state.scannedData) return;
        if (e.target.checked) {
            state.scannedData.files.forEach(f => state.selectedFiles.add(f.path));
        } else {
            state.selectedFiles.clear();
        }
        renderFilesTable(state.scannedData.files);
    });

    // Preview & Organize Buttons
    elements.btnPreviewDryrun.addEventListener('click', runDryRunPreview);
    elements.btnExecuteOrganize.addEventListener('click', executeOrganization);
    elements.btnModalConfirmExecute.addEventListener('click', executeOrganization);

    // Modals Close
    elements.modalClose.addEventListener('click', () => elements.previewModal.classList.remove('active'));
    elements.btnModalCancel.addEventListener('click', () => elements.previewModal.classList.remove('active'));
    elements.batchModalClose.addEventListener('click', () => elements.batchDetailsModal.classList.remove('active'));
    elements.btnBatchModalClose.addEventListener('click', () => elements.batchDetailsModal.classList.remove('active'));

    // Create Sandbox Buttons
    const handleCreateSandbox = async () => {
        try {
            showToast('Creating demo sandbox with sample files...', 'info');
            const res = await fetch('/api/demo-sandbox', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                elements.targetFolderInput.value = data.path;
                showToast(data.message, 'success');
                // Switch to Organizer tab if not active
                document.querySelector('.nav-item[data-tab="tab-organizer"]')?.click();
                await scanCurrentDirectory();
            } else {
                showToast(data.error || 'Failed to create sandbox', 'error');
            }
        } catch (err) {
            showToast('Error creating sandbox: ' + err.message, 'error');
        }
    };

    elements.btnCreateSandbox.addEventListener('click', handleCreateSandbox);
    elements.btnEmptySandbox.addEventListener('click', handleCreateSandbox);

    // Watcher Start Button
    elements.btnStartWatcher.addEventListener('click', async () => {
        const folder = elements.watcherFolderInput.value.trim() || elements.targetFolderInput.value.trim();
        if (!folder) {
            showToast('Please enter a folder path to watch', 'error');
            return;
        }
        await startWatcherFolder(folder, elements.watcherStrategySelect.value);
        elements.watcherFolderInput.value = '';
    });
    elements.btnRefreshWatchers.addEventListener('click', fetchWatchers);
    elements.btnRefreshHistory.addEventListener('click', fetchHistory);
    elements.btnRefreshLogs.addEventListener('click', fetchLogs);
    elements.btnClearLogsView.addEventListener('click', () => elements.terminalBody.innerHTML = '');

    // Form Create Custom Rule
    elements.formCreateRule.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('rule-name').value.trim(),
            condition_type: document.getElementById('rule-condition').value,
            pattern: document.getElementById('rule-pattern').value.trim(),
            target_folder: document.getElementById('rule-target').value.trim(),
            priority: parseInt(document.getElementById('rule-priority').value, 10) || 10
        };

        try {
            const res = await fetch('/api/rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                showToast('Custom sorting rule created successfully!', 'success');
                elements.formCreateRule.reset();
                initCustomRules();
            } else {
                showToast(data.error || 'Failed to create rule', 'error');
            }
        } catch (err) {
            showToast('Error adding rule: ' + err.message, 'error');
        }
    });
}

// Toast System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Helper Utilities
function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJs(str) {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}
