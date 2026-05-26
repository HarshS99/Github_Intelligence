/* ── Config ───────────────────────────────────────────────── */
const API = 'http://localhost:8000';
let busy = false;

/* ── Status polling ───────────────────────────────────────── */
async function checkStatus() {
  try {
    const r = await fetch(`${API}/status`, { signal: AbortSignal.timeout(4000) });
    const d = await r.json();
    setDot('dotApi', 'lblApi', true, 'API online');
    setDot('dotGh',  'lblGh',  d.github_token,
      d.github_token ? 'GitHub ✓' : 'No token');
  } catch {
    setDot('dotApi', 'lblApi', false, 'API offline');
    setDot('dotGh',  'lblGh',  false, 'GitHub');
  }
}

function setDot(dotId, lblId, ok, label) {
  document.getElementById(dotId).className = 'dot ' + (ok ? 'on' : 'off');
  document.getElementById(lblId).textContent = label;
}

checkStatus();
setInterval(checkStatus, 20000);

/* ── Toast ────────────────────────────────────────────────── */
let _toastTimer;
function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (type ? ' ' + type : '');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { t.className = 'toast'; }, 4000);
}

/* ── DOM helpers ──────────────────────────────────────────── */
function $(id) { return document.getElementById(id); }

function removeWelcome() {
  const w = $('welcome');
  if (w) w.remove();
}

function esc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function scrollBottom() {
  const m = $('messages');
  m.scrollTop = m.scrollHeight;
}

/* ── Message renderers ────────────────────────────────────── */
function addMsg(role, text, isError = false) {
  removeWelcome();
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML =
    `<div class="msg-who">${role === 'user' ? 'You' : '🐙 GitHub AI'}</div>` +
    `<div class="msg-body${isError ? ' error' : ''}">${esc(text)}</div>`;
  $('messages').appendChild(div);
  scrollBottom();
}

function addCard(innerHtml, colorClass = '') {
  removeWelcome();
  const div = document.createElement('div');
  div.className = 'result-card ' + colorClass;
  div.innerHTML = innerHtml;
  $('messages').appendChild(div);
  scrollBottom();
}

function addTyping() {
  removeWelcome();
  const wrap = document.createElement('div');
  wrap.className = 'typing-wrap';
  wrap.id = '_typing';
  wrap.innerHTML =
    `<div class="msg-who">🐙 GitHub AI</div>` +
    `<div class="typing"><span></span><span></span><span></span></div>`;
  $('messages').appendChild(wrap);
  scrollBottom();
}

function removeTyping() {
  const el = $('_typing');
  if (el) el.remove();
}

/* ── Busy state ───────────────────────────────────────────── */
function setBusy(b) {
  busy = b;
  $('sendBtn').disabled = b;
  $('sendBtn').textContent = b ? '…' : 'Send ↑';
}

/* ── API fetch wrapper ────────────────────────────────────── */
async function apiFetch(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(130_000),
  };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  const json = await r.json();
  if (!r.ok) throw new Error(json.error || `HTTP ${r.status}`);
  return json;
}

/* ── Chat ─────────────────────────────────────────────────── */
function sendChat() {
  if (busy) return;
  const ta = $('chatInput');
  const text = ta.value.trim();
  if (!text) return;
  ta.value = '';
  ta.style.height = '';
  chat(text);
}

async function chat(message) {
  if (busy) return;
  addMsg('user', message);
  setBusy(true);
  addTyping();
  try {
    const d = await apiFetch('/chat', 'POST', { message });
    removeTyping();
    addMsg('bot', d.response || 'No response.');
  } catch (e) {
    removeTyping();
    const msg = e.name === 'TimeoutError'
      ? '⏱️ Timed out — try a simpler question.'
      : '❌ ' + e.message;
    addMsg('bot', msg, true);
    showToast(msg, 'err');
  } finally {
    setBusy(false);
  }
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
}

/* Auto-resize textarea */
$('chatInput').addEventListener('input', function () {
  this.style.height = '';
  this.style.height = Math.min(this.scrollHeight, 140) + 'px';
});

/* ── Analyze repo ─────────────────────────────────────────── */
async function doAnalyze() {
  const repo = $('inAnalyze').value.trim();
  if (!repo) return showToast('Enter a repo: owner/repo', 'err');
  if (!repo.includes('/')) return showToast('Format: owner/repo  e.g. facebook/react', 'err');
  if (busy) return;
  addMsg('user', `Analyze: ${repo}`);
  setBusy(true);
  addTyping();
  try {
    const d = await apiFetch('/analyze', 'POST', { repository: repo });
    removeTyping();
    const i = d.info || {};
    const header =
      `<h4>📊 ${esc(i.name || repo)}</h4>` +
      `⭐ ${(i.stars || 0).toLocaleString()}  ` +
      `🍴 ${(i.forks || 0).toLocaleString()}  ` +
      `🐛 ${i.open_issues || 0} issues  ` +
      `🌐 ${esc(i.language || '?')}\n\n`;
    addCard(header + esc(d.analysis || 'No analysis.'), 'green');
  } catch (e) {
    removeTyping();
    addMsg('bot', '❌ ' + e.message, true);
    showToast('❌ ' + e.message, 'err');
  } finally { setBusy(false); }
}

/* ── User profile ─────────────────────────────────────────── */
async function doUser() {
  const username = $('inUser').value.trim();
  if (!username) return showToast('Enter a GitHub username', 'err');
  if (busy) return;
  addMsg('user', `Profile: ${username}`);
  setBusy(true);
  addTyping();
  try {
    const d = await apiFetch(`/user/${encodeURIComponent(username)}`);
    removeTyping();
    const p = d.profile || {};
    let html = `<h4>👤 ${esc(p.name || p.username || username)}</h4>`;
    if (p.bio)      html += esc(p.bio) + '\n';
    if (p.company)  html += `🏢 ${esc(p.company)}\n`;
    if (p.location) html += `📍 ${esc(p.location)}\n`;
    html += `\nFollowers: ${(p.followers || 0).toLocaleString()}  ·  Public repos: ${p.public_repos || 0}`;
    if (d.top_repos && d.top_repos.length) {
      html += '\n\nTop repositories:\n' + d.top_repos.map(r =>
        `  ⭐ ${r.stars}  ${esc(r.name)}` +
        (r.language ? `  [${esc(r.language)}]` : '') +
        (r.description ? `\n     ${esc(r.description)}` : '')
      ).join('\n');
    }
    addCard(html);
  } catch (e) {
    removeTyping();
    addMsg('bot', '❌ ' + e.message, true);
    showToast('❌ ' + e.message, 'err');
  } finally { setBusy(false); }
}

/* ── Search ───────────────────────────────────────────────── */
async function doSearch() {
  const query = $('inSearch').value.trim();
  if (!query) return showToast('Enter a search query', 'err');
  if (busy) return;
  addMsg('user', `Search: ${query}`);
  setBusy(true);
  addTyping();
  try {
    const d = await apiFetch('/search', 'POST', { query });
    removeTyping();
    const results = d.results || [];
    if (!results.length) { addMsg('bot', 'No results found.'); return; }
    let html = `<h4>🔎 "${esc(query)}" — ${results.length} results</h4>`;
    html += results.map(r =>
      `⭐ ${(r.stars || 0).toLocaleString()}  <b style="color:var(--blue-h)">${esc(r.name)}</b>` +
      (r.language ? `  [${esc(r.language)}]` : '') +
      `\n  ${esc(r.description)}`
    ).join('\n\n');
    addCard(html);
  } catch (e) {
    removeTyping();
    addMsg('bot', '❌ ' + e.message, true);
    showToast('❌ ' + e.message, 'err');
  } finally { setBusy(false); }
}

/* ── Issues ───────────────────────────────────────────────── */
async function doIssues() {
  const repo = $('inIssues').value.trim();
  if (!repo) return showToast('Enter owner/repo', 'err');
  if (busy) return;
  addMsg('user', `Open issues: ${repo}`);
  setBusy(true);
  addTyping();
  try {
    const d = await apiFetch(`/issues/${repo}`);
    removeTyping();
    const issues = d.issues || [];
    if (!issues.length) { addMsg('bot', `No open issues in ${repo}.`); return; }
    let html = `<h4>🐛 Open Issues — ${esc(repo)} (${issues.length})</h4>`;
    html += issues.map(i =>
      `#${i.number}  ${esc(i.title)}` +
      (i.labels.length ? `  [${i.labels.map(esc).join(', ')}]` : '') +
      `\n  ${i.created_at.slice(0, 10)}`
    ).join('\n\n');
    addCard(html);
  } catch (e) {
    removeTyping();
    addMsg('bot', '❌ ' + e.message, true);
    showToast('❌ ' + e.message, 'err');
  } finally { setBusy(false); }
}

/* ── Pull requests ────────────────────────────────────────── */
async function doPulls() {
  const repo = $('inIssues').value.trim();
  if (!repo) return showToast('Enter owner/repo', 'err');
  if (busy) return;
  addMsg('user', `Open PRs: ${repo}`);
  setBusy(true);
  addTyping();
  try {
    const d = await apiFetch(`/pulls/${repo}`);
    removeTyping();
    const pulls = d.pulls || [];
    if (!pulls.length) { addMsg('bot', `No open PRs in ${repo}.`); return; }
    let html = `<h4>🔀 Open Pull Requests — ${esc(repo)} (${pulls.length})</h4>`;
    html += pulls.map(p =>
      `#${p.number}  ${esc(p.title)}\n  by @${esc(p.author)}  ·  ${p.created_at.slice(0, 10)}`
    ).join('\n\n');
    addCard(html);
  } catch (e) {
    removeTyping();
    addMsg('bot', '❌ ' + e.message, true);
    showToast('❌ ' + e.message, 'err');
  } finally { setBusy(false); }
}

/* ── Trending ─────────────────────────────────────────────── */
async function doTrending(lang) {
  if (busy) return;
  const label = lang ? lang.charAt(0).toUpperCase() + lang.slice(1) : 'All';
  addMsg('user', `Trending — ${label}`);
  setBusy(true);
  addTyping();
  try {
    const qs = lang ? `?language=${encodeURIComponent(lang)}` : '';
    const d = await apiFetch(`/trending${qs}`);
    removeTyping();
    const results = d.results || [];
    if (!results.length || results[0].error) {
      addMsg('bot', results[0]?.error || 'No trending data.', true);
      return;
    }
    let html = `<h4>🔥 Trending — ${esc(label)}</h4>`;
    html += results.map((r, i) =>
      `${i + 1}. <b style="color:var(--blue-h)">${esc(r.name)}</b>` +
      (r.stars_today ? `  +${esc(r.stars_today)} today` :
       r.stars ? `  ⭐ ${(r.stars || 0).toLocaleString()}` : '') +
      `\n   ${esc(r.description || 'No description')}`
    ).join('\n\n');
    addCard(html, 'green');
  } catch (e) {
    removeTyping();
    addMsg('bot', '❌ ' + e.message, true);
    showToast('❌ ' + e.message, 'err');
  } finally { setBusy(false); }
}

/* ── Clear session ────────────────────────────────────────── */
async function doClear() {
  try {
    await apiFetch('/clear', 'POST');
    addMsg('bot', '🧹 Session cleared.');
    showToast('Cleared', 'ok');
  } catch (e) {
    showToast('Failed: ' + e.message, 'err');
  }
}