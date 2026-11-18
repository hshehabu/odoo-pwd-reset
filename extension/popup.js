// Odoo Reset Hub popup. Talks to the local Python helper through Chrome Native
// Messaging; Chrome starts the helper itself, so nothing needs to be running.

const HOST = 'com.odoo.reset_hub';
const $ = (id) => document.getElementById(id);

let port = null;
let nextId = 1;
const pending = new Map();
let tabInfo = null; // { tabId, origin, db }

function connect() {
    port = chrome.runtime.connectNative(HOST);
    port.onMessage.addListener((msg) => {
        const p = pending.get(msg.id);
        if (p) { pending.delete(msg.id); p.resolve(msg); }
    });
    port.onDisconnect.addListener(() => {
        const err = chrome.runtime.lastError?.message || 'Helper stopped';
        port = null;
        if (/not found|forbidden/i.test(err)) {
            $('setupNotice').hidden = false;
        }
        setStatus('error', err);
        pending.forEach((p) => p.resolve({ success: false, error: err }));
        pending.clear();
    });
}

function call(action, params = {}) {
    if (!port) connect();
    const id = nextId++;
    return new Promise((resolve) => {
        pending.set(id, { resolve });
        try {
            port.postMessage({ id, action, ...params });
        } catch (e) {
            pending.delete(id);
            resolve({ success: false, error: e.message });
        }
    });
}

function setStatus(state, title) {
    $('status').className = `status ${state}`;
    $('status').title = title;
}

function showMsg(type, title, body = '') {
    const box = $('msg');
    box.className = `notice ${type}`;
    box.replaceChildren();
    const t = document.createElement('strong');
    t.textContent = title;
    box.append(t, body);
    box.hidden = false;
}

// ---------- active tab detection ----------

async function detectTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.url || !/^https?:/.test(tab.url)) return null;
    const url = new URL(tab.url);

    let db = url.searchParams.get('db');
    if (!db) {
        try {
            const [res] = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                world: 'MAIN',
                func: () => {
                    const o = window.odoo || {};
                    const s = o.__session_info__ || o.session_info || window.session_info || {};
                    return s.db || o.info?.db || null;
                },
            });
            db = res?.result || null;
        } catch (e) { /* not scriptable */ }
    }
    if (!db) {
        try {
            const c = await chrome.cookies.get({ url: tab.url, name: 'last_used_database' });
            db = c?.value || null;
        } catch (e) { /* ignore */ }
    }
    return { tabId: tab.id, origin: url.origin, db };
}

// ---------- database list & meta ----------

let catalog = {};

async function loadDatabases() {
    const res = await call('databases');
    if (!res.success) {
        setStatus('error', res.error);
        if ($('setupNotice').hidden) showMsg('error', 'Could not load databases', res.error);
        return;
    }
    setStatus('ok', 'Helper ready');
    catalog = {};
    for (const d of res.databases) catalog[d.name] = d;
    updateMeta();
    if (!$('dbList').hidden) renderDropdown();
}

// ---------- database dropdown ----------

let activeIdx = -1;

function matches() {
    const q = $('db').value.trim().toLowerCase();
    const all = Object.values(catalog);
    if (!q || catalog[$('db').value.trim()]) return all; // exact pick: show everything
    return all.filter((d) => d.name.toLowerCase().includes(q));
}

function renderDropdown() {
    const list = $('dbList');
    const items = matches();
    list.replaceChildren();
    activeIdx = -1;
    if (!items.length) {
        const li = document.createElement('li');
        li.className = 'empty';
        li.textContent = Object.keys(catalog).length ? 'No matching database' : 'Loading…';
        list.append(li);
    }
    items.forEach((d, i) => {
        const li = document.createElement('li');
        li.role = 'option';
        const name = document.createElement('span');
        name.className = 'name';
        name.textContent = d.name;
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = `${d.owner} · ${d.suggested_version}`;
        li.append(name, tag);
        li.addEventListener('mousedown', (e) => { e.preventDefault(); pick(d.name); });
        li.addEventListener('mousemove', () => setActive(i));
        if (d.name === $('db').value.trim()) activeIdx = i;
        list.append(li);
    });
    setActive(activeIdx);
}

function openDropdown() {
    $('dbList').hidden = false;
    $('db').setAttribute('aria-expanded', 'true');
    renderDropdown();
}

function closeDropdown() {
    $('dbList').hidden = true;
    $('db').setAttribute('aria-expanded', 'false');
}

function setActive(i) {
    const lis = $('dbList').querySelectorAll('li[role="option"]');
    lis.forEach((li, j) => li.classList.toggle('active', j === i));
    activeIdx = i;
    if (lis[i]) lis[i].scrollIntoView({ block: 'nearest' });
}

function pick(name) {
    $('db').value = name;
    closeDropdown();
    updateMeta();
}

function onDbKey(e) {
    const open = !$('dbList').hidden;
    const count = $('dbList').querySelectorAll('li[role="option"]').length;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!open) return openDropdown();
        if (!count) return;
        const step = e.key === 'ArrowDown' ? 1 : -1;
        setActive((activeIdx + step + count) % count);
    } else if (e.key === 'Enter' && open && activeIdx >= 0) {
        e.preventDefault();
        pick(matches()[activeIdx].name);
    } else if (e.key === 'Escape' && open) {
        e.preventDefault();
        closeDropdown();
    }
}

function updateMeta() {
    const name = $('db').value.trim();
    const d = catalog[name];
    let text = '';
    if (d) text = `Owner ${d.owner} · v${d.suggested_version}`;
    else if (name && Object.keys(catalog).length) text = 'Not found in PostgreSQL';
    if (tabInfo?.db && tabInfo.db === name) text = `From current tab · ${text}`.replace(/ · $/, '');
    $('dbMeta').textContent = text;
}

// ---------- reset ----------

async function onSubmit(e) {
    e.preventDefault();
    const db = $('db').value.trim();
    const login = $('login').value.trim();
    const password = $('password').value;
    if (!db) return;

    const btn = $('submit');
    btn.disabled = true;
    btn.textContent = 'Resetting…';
    $('msg').hidden = true;

    const res = await call('reset', {
        dbname: db,
        login,
        new_password: password,
        version: $('version').value,
        user_id: parseInt($('userId').value, 10) || 2,
        db_user: $('dbUser').value.trim(),
    });

    btn.disabled = false;
    btn.textContent = 'Reset password';

    if (!res.success) {
        showMsg('error', 'Reset failed', res.error || 'Unknown error');
        return;
    }

    chrome.storage.local.set({ login, password, autoLogin: $('autoLogin').checked });

    const det = res.details || {};
    const ver = det.detected_version ? ` · v${det.detected_version}` : '';
    showMsg('ok', 'Password reset', `${login} / ${password} on ${db} (pg user ${det.db_user}${ver})`);

    if ($('autoLogin').checked && tabInfo && tabInfo.db === db) {
        chrome.runtime.sendMessage({ type: 'login', tabId: tabInfo.tabId, origin: tabInfo.origin, db, login, password });
        setTimeout(() => window.close(), 400);
    }
}

// ---------- init ----------

document.addEventListener('DOMContentLoaded', async () => {
    $('form').addEventListener('submit', onSubmit);
    const db = $('db');
    db.addEventListener('input', () => { updateMeta(); openDropdown(); });
    db.addEventListener('click', openDropdown);
    db.addEventListener('blur', closeDropdown);
    db.addEventListener('keydown', onDbKey);

    const stored = await chrome.storage.local.get(['login', 'password', 'autoLogin']);
    if (stored.login) $('login').value = stored.login;
    if (stored.password) $('password').value = stored.password;
    if (stored.autoLogin === false) $('autoLogin').checked = false;

    // Run both in parallel: the helper starts while we inspect the tab.
    const dbsPromise = loadDatabases();
    tabInfo = await detectTab();
    if (tabInfo?.db && !$('db').value) {
        $('db').value = tabInfo.db;
        updateMeta();
    }
    $('autoLogin').closest('label').hidden = !tabInfo?.db;
    await dbsPromise;
});
