// Handles the post-reset login so it keeps working after the popup closes.

function fillAndSubmit(login, password) {
    const form = document.querySelector('form.oe_login_form') || document.querySelector('form[action*="/web/login"]');
    if (!form) return false;
    const set = (el, val) => {
        if (!el) return;
        el.value = val;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    };
    set(form.querySelector('input[name="login"]'), login);
    set(form.querySelector('input[name="password"]'), password);
    const btn = form.querySelector('button[type="submit"]');
    btn ? btn.click() : form.submit();
    return true;
}

async function tryFill(tabId, login, password) {
    const [res] = await chrome.scripting.executeScript({
        target: { tabId },
        func: fillAndSubmit,
        args: [login, password],
    });
    return res && res.result;
}

function waitForLoginPage(tabId, timeoutMs = 15000) {
    return new Promise((resolve) => {
        const timer = setTimeout(() => { chrome.tabs.onUpdated.removeListener(onUpd); resolve(false); }, timeoutMs);
        function onUpd(id, info, tab) {
            if (id !== tabId || info.status !== 'complete') return;
            if (!/\/web\/login/.test(tab.url || '')) return;
            clearTimeout(timer);
            chrome.tabs.onUpdated.removeListener(onUpd);
            resolve(true);
        }
        chrome.tabs.onUpdated.addListener(onUpd);
    });
}

async function loginInTab({ tabId, origin, db, login, password }) {
    // Already on the login form? Fill it right away.
    try {
        if (await tryFill(tabId, login, password)) return;
    } catch (e) { /* page not scriptable, fall through */ }

    // Otherwise end the current session and go to the login page for this db.
    const loginPath = `/web/login?db=${encodeURIComponent(db)}`;
    const url = `${origin}/web/session/logout?redirect=${encodeURIComponent(loginPath)}`;
    const loaded = waitForLoginPage(tabId);
    await chrome.tabs.update(tabId, { url });
    if (await loaded) {
        try { await tryFill(tabId, login, password); } catch (e) { console.warn('Autofill failed', e); }
    }
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.type === 'login') {
        loginInTab(msg).finally(() => sendResponse({ ok: true }));
        return true;
    }
});
