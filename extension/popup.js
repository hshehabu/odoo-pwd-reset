/**
 * Odoo Password Reset Extension - popup.js
 * Works seamlessly across Odoo v16, v17, v18, and v19
 */

const VERSION_USER_MAP = {
    'auto': 'auto-detect',
    '16': 'openpg16',
    '17': 'openpg17',
    '18': 'openpg',
    '19': 'openpg'
};

let currentVersion = 'auto';
let databaseCatalog = {};
let detectedTabInfo = null;
let apiUrl = 'http://127.0.0.1:1111';

// DOM Elements
const serverBadge = document.getElementById('serverBadge');
const serverBadgeText = document.getElementById('serverBadgeText');
const offlineNotice = document.getElementById('offlineNotice');
const retryBtn = document.getElementById('retryBtn');

const activeTabCard = document.getElementById('activeTabCard');
const activeTabDb = document.getElementById('activeTabDb');
const useDetectedDbBtn = document.getElementById('useDetectedDbBtn');

const dbInput = document.getElementById('dbInput');
const databasesList = document.getElementById('databasesList');
const refreshDbsBtn = document.getElementById('refreshDbsBtn');
const dbMetaInfo = document.getElementById('dbMetaInfo');
const metaOwner = document.getElementById('metaOwner');
const metaVersion = document.getElementById('metaVersion');

const activeUserBadge = document.getElementById('activeUserBadge');
const versionPills = document.querySelectorAll('.version-pill');

const loginInput = document.getElementById('loginInput');
const pwdInput = document.getElementById('pwdInput');
const togglePwdBtn = document.getElementById('togglePwdBtn');
const userIdInput = document.getElementById('userIdInput');
const customDbUser = document.getElementById('customDbUser');
const apiUrlInput = document.getElementById('apiUrlInput');

const resetForm = document.getElementById('resetForm');
const submitBtn = document.getElementById('submitBtn');
const alertBox = document.getElementById('alertBox');
const postActionBox = document.getElementById('postActionBox');
const autofillBtn = document.getElementById('autofillBtn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load stored settings
    try {
        const stored = await chrome.storage.local.get(['apiUrl', 'lastVersion', 'lastLogin']);
        if (stored.apiUrl) {
            apiUrl = stored.apiUrl;
            apiUrlInput.value = apiUrl;
        }
        if (stored.lastVersion) {
            setVersion(stored.lastVersion);
        }
        if (stored.lastLogin) {
            loginInput.value = stored.lastLogin;
        }
    } catch (e) {
        console.warn('Storage read fallback', e);
    }

    // Detect Active Tab Odoo
    detectActiveTabOdoo();

    // Check Backend Server & Load Databases
    checkServerAndLoadDbs();

    // Setup Event Listeners
    setupEvents();
});

function setupEvents() {
    // Retry server button
    retryBtn.addEventListener('click', checkServerAndLoadDbs);

    // Refresh databases button
    refreshDbsBtn.addEventListener('click', () => {
        refreshDbsBtn.style.transform = 'rotate(360deg)';
        refreshDbsBtn.style.transition = 'transform 0.4s';
        setTimeout(() => refreshDbsBtn.style.transform = 'none', 400);
        loadDatabases();
    });

    // Version pill selection
    versionPills.forEach(pill => {
        pill.addEventListener('click', () => {
            const v = pill.getAttribute('data-version');
            setVersion(v);
        });
    });

    // Toggle password visibility
    togglePwdBtn.addEventListener('click', () => {
        if (pwdInput.type === 'password') {
            pwdInput.type = 'text';
            togglePwdBtn.textContent = '🔒';
        } else {
            pwdInput.type = 'password';
            togglePwdBtn.textContent = '👁️';
        }
    });

    // Preset password buttons
    document.querySelectorAll('.preset-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            pwdInput.value = tag.getAttribute('data-val');
        });
    });

    // Database input changes
    dbInput.addEventListener('input', () => {
        updateDbMetaDisplay();
    });

    // Use detected database button
    useDetectedDbBtn.addEventListener('click', () => {
        if (detectedTabInfo && detectedTabInfo.db) {
            dbInput.value = detectedTabInfo.db;
            if (detectedTabInfo.version) {
                const major = detectedTabInfo.version.split('.')[0];
                if (['16', '17', '18', '19'].includes(major)) {
                    setVersion(major);
                }
            }
            updateDbMetaDisplay();
        }
    });

    // API URL input changed
    apiUrlInput.addEventListener('change', () => {
        apiUrl = apiUrlInput.value.trim().replace(/\/+$/, '');
        chrome.storage.local.set({ apiUrl });
        checkServerAndLoadDbs();
    });

    // Form submit
    resetForm.addEventListener('submit', handleResetPassword);

    // Post-reset autofill button
    autofillBtn.addEventListener('click', handleAutofillTab);
}

function setVersion(ver) {
    currentVersion = ver;
    versionPills.forEach(p => {
        if (p.getAttribute('data-version') === ver) {
            p.classList.add('active');
        } else {
            p.classList.remove('active');
        }
    });
    updateUserBadge();
    chrome.storage.local.set({ lastVersion: ver });
}

function updateUserBadge() {
    const dbVal = dbInput.value.trim();
    if (currentVersion === 'auto') {
        if (databaseCatalog[dbVal]) {
            const meta = databaseCatalog[dbVal];
            activeUserBadge.textContent = `DB User: ${meta.owner}`;
        } else {
            activeUserBadge.textContent = 'DB User: auto-detect';
        }
    } else {
        activeUserBadge.textContent = `DB User: ${VERSION_USER_MAP[currentVersion] || 'openpg'}`;
    }
}

function updateDbMetaDisplay() {
    const dbVal = dbInput.value.trim();
    if (databaseCatalog[dbVal]) {
        const meta = databaseCatalog[dbVal];
        metaOwner.textContent = meta.owner;
        metaVersion.textContent = meta.suggested_version;
        dbMetaInfo.style.display = 'block';
    } else {
        dbMetaInfo.style.display = 'none';
    }
    updateUserBadge();
}

async function checkServerAndLoadDbs() {
    setServerStatus('checking', 'Connecting...');
    offlineNotice.style.display = 'none';

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const res = await fetch(`${apiUrl}/api/status`, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (res.ok) {
            setServerStatus('online', 'Connected');
            offlineNotice.style.display = 'none';
            loadDatabases();
        } else {
            throw new Error(`Server returned status ${res.status}`);
        }
    } catch (err) {
        setServerStatus('offline', 'Offline');
        offlineNotice.style.display = 'flex';
    }
}

function setServerStatus(state, label) {
    serverBadge.className = `status-badge ${state}`;
    serverBadgeText.textContent = label;
}

async function loadDatabases() {
    try {
        const res = await fetch(`${apiUrl}/api/databases`);
        const data = await res.json();
        if (data.success && Array.isArray(data.databases)) {
            databaseCatalog = {};
            databasesList.innerHTML = '';
            data.databases.forEach(db => {
                databaseCatalog[db.name] = db;
                const opt = document.createElement('option');
                opt.value = db.name;
                opt.label = `${db.name} (${db.owner} - ${db.suggested_version})`;
                databasesList.appendChild(opt);
            });
            updateDbMetaDisplay();
        }
    } catch (e) {
        console.warn('Failed to load databases:', e);
    }
}

// Active Tab Odoo Detection
async function detectActiveTabOdoo() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.url || tab.url.startsWith('chrome://')) return;

        // Try getting last_used_database cookie first
        let cookieDb = null;
        try {
            const cookie = await chrome.cookies.get({ url: tab.url, name: 'last_used_database' });
            if (cookie && cookie.value) {
                cookieDb = cookie.value;
            }
        } catch (e) {}

        // Inspect page context for window.odoo session_info
        let pageDb = null;
        let pageVersion = null;
        try {
            const results = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                world: 'MAIN',
                func: () => {
                    try {
                        const odoo = window.odoo;
                        const session = odoo?.session_info || window.session_info;
                        return {
                            db: session?.db || (document.cookie.match(/last_used_database=([^;]+)/)?.[1]),
                            version: session?.server_version || null,
                            isOdoo: !!(window.odoo || document.querySelector('link[href*="web/content"]') || document.title.includes('Odoo'))
                        };
                    } catch (e) {
                        return null;
                    }
                }
            });

            if (results && results[0] && results[0].result) {
                const res = results[0].result;
                if (res.db) pageDb = res.db;
                if (res.version) pageVersion = res.version;
            }
        } catch (e) {}

        const finalDb = pageDb || cookieDb;
        if (finalDb) {
            detectedTabInfo = {
                tabId: tab.id,
                db: finalDb,
                version: pageVersion
            };
            activeTabDb.textContent = `${finalDb} ${pageVersion ? '(' + pageVersion + ')' : ''}`;
            activeTabCard.style.display = 'flex';

            // Auto-fill dbInput if currently empty
            if (!dbInput.value) {
                dbInput.value = finalDb;
                if (pageVersion) {
                    const major = pageVersion.split('.')[0];
                    if (['16', '17', '18', '19'].includes(major)) {
                        setVersion(major);
                    }
                }
                updateDbMetaDisplay();
            }
        }
    } catch (err) {
        console.warn('Tab detection error:', err);
    }
}

// Reset Password Handler
async function handleResetPassword(e) {
    e.preventDefault();

    const dbname = dbInput.value.trim();
    const login = loginInput.value.trim();
    const new_password = pwdInput.value;
    const user_id = userIdInput.value ? parseInt(userIdInput.value) : 2;
    const customUser = customDbUser.value.trim() || undefined;

    if (!dbname) {
        showAlert('Please enter or select a database name.', 'error');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-text">Resetting...</span>';
    showAlert('Connecting to database and hashing password with PBKDF2-SHA512...', 'info');
    postActionBox.style.display = 'none';

    try {
        const res = await fetch(`${apiUrl}/api/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dbname,
                version: currentVersion,
                db_user: customUser,
                login,
                new_password,
                user_id
            })
        });

        const data = await res.json();
        if (data.success) {
            const det = data.details || {};
            showAlert(`
                <strong>🎉 Password Reset Successful!</strong><br>
                <span>DB: <strong>${det.database}</strong> | User: <strong>${det.db_user}</strong></span><br>
                <span>Login: <strong>${det.login}</strong> | Password: <strong>${new_password}</strong></span>
            `, 'success');

            // Save last used login
            chrome.storage.local.set({ lastLogin: login });

            // Show Auto-Fill button if on an active tab
            postActionBox.style.display = 'block';
        } else {
            showAlert(`<strong>Failed:</strong> ${data.error || 'Unknown error occurred'}`, 'error');
        }
    } catch (err) {
        showAlert(`<strong>Error:</strong> Cannot reach local server at ${apiUrl}. Please make sure <code>start_background.vbs</code> or <code>start_server.bat</code> is running.`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-text">Reset Password</span>';
    }
}

// Auto-fill credentials in the active tab
async function handleAutofillTab() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.id) return;

        const login = loginInput.value.trim();
        const pwd = pwdInput.value;

        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: (loginVal, pwdVal) => {
                // Find login field
                const loginEl = document.querySelector('input[name="login"], #login, input[autocomplete="username"]');
                const pwdEl = document.querySelector('input[name="password"], #password, input[type="password"]');

                if (loginEl) {
                    loginEl.value = loginVal;
                    loginEl.dispatchEvent(new Event('input', { bubbles: true }));
                    loginEl.dispatchEvent(new Event('change', { bubbles: true }));
                }
                if (pwdEl) {
                    pwdEl.value = pwdVal;
                    pwdEl.dispatchEvent(new Event('input', { bubbles: true }));
                    pwdEl.dispatchEvent(new Event('change', { bubbles: true }));
                }

                // If on login form, click submit
                const submitBtn = document.querySelector('button[type="submit"], .oe_login_buttons button');
                if (submitBtn) {
                    submitBtn.click();
                } else {
                    window.location.reload();
                }
            },
            args: [login, pwd]
        });

        window.close(); // Close extension popup
    } catch (e) {
        console.warn('Autofill error:', e);
        showAlert('Could not auto-fill tab (must be on an Odoo login page).', 'info');
    }
}

function showAlert(html, type) {
    alertBox.innerHTML = html;
    alertBox.className = `alert-box ${type}`;
    alertBox.style.display = 'block';
}

