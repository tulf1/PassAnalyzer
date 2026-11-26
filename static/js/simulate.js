"use strict";

const PILL = {
  "Very Weak": ["#3A0E16", "#FF5470"],
  "Weak":      ["#3A1E0A", "#FFB067"],
  "Fair":      ["#2E2A0A", "#FFE066"],
  "Strong":    ["#0C2E1F", "#39FF88"],
  "Very Strong": ["#06262E", "#5CE1FF"],
};
const CLASS_COLOR = {
  "Very Weak": "#FF5470", "Weak": "#FF8A3D", "Fair": "#FFD23F",
  "Strong": "#39FF88", "Very Strong": "#00B8FF",
};
const ORDER = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"];

const $ = (id) => document.getElementById(id);

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => (
    {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]
  ));
}

function renderClasses(summary, count) {
  $("sample-sub").textContent = `for your sample of ${count}`;
  const rows = ORDER.filter(k => summary[k]).map(k => {
    const b = summary[k];
    const pct = b.total ? Math.round((b.cracked / b.total) * 100) : 0;
    const col = CLASS_COLOR[k];
    return `<div class="crack-line">
      <span class="name">${k}</span>
      <div class="bar" style="flex:1"><span style="width:${pct}%; background:${col}"></span></div>
      <span class="val">${b.cracked} / ${b.total} (${pct}%)</span>
    </div>`;
  });
  $("classes").innerHTML = rows.length ? rows.join("") : `<p class="hint">No accounts in this sample.</p>`;
}

function renderResults(rows) {
  if (!rows.length) { $("results").innerHTML = `<tr><td class="muted" colspan="5">No rows.</td></tr>`; return; }
  $("results").innerHTML = rows.map(r => {
    const [bg, fg] = PILL[r.rating] || ["#15202A", "#E6F1F5"];
    const cc = r.cracked ? "#FF5470" : "#39FF88";
    return `<tr>
      <td class="mono">${escapeHtml(r.username)}</td>
      <td><span class="pill" style="background:${bg}; color:${fg}; font-size:12px">${r.rating}</span></td>
      <td style="font-weight:700; color:${cc}">${r.cracked ? "✓ yes" : "✗ no"}</td>
      <td class="right mono">${Number(r.attempts).toLocaleString()}</td>
      <td class="mono">${r.found_as ? escapeHtml(r.found_as) : "—"}</td>
    </tr>`;
  }).join("");
}

function clampCount() {
  const el = $("count");
  let n = Math.round(Number(el.value) || 0);
  const max = Number(el.max) || 1000;
  if (n < 1) n = 1;
  if (n > max) n = max;
  el.value = n;
  return n;
}

async function run(mode) {
  const count = clampCount();
  $("status").style.display = "flex";
  $("note").textContent = `Attacking a random sample of ${count} accounts…`;
  try {
    const resp = await fetch("/api/simulate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({mode: mode, count: count}),
    });
    if (!resp.ok) { $("note").textContent = "The run could not be completed."; return; }
    const d = await resp.json();
    $("wsize").textContent = Number(d.wordlist_size).toLocaleString();
    $("cracked-total").textContent = `${d.cracked_total} / ${d.count}`;
    renderClasses(d.summary, d.count);
    renderResults(d.results);
    $("note").textContent = `Attacked ${d.count} of the database's accounts. Whole accounts only (1 to ${$("count").max}).`;
  } catch (e) {
    $("note").textContent = "The run could not be completed.";
  } finally {
    $("status").style.display = "none";
  }
}

const ATTACK_BTN = { dictionary: "attack-dict", bruteforce: "attack-brute" };
const ATTACK_LABEL = { dictionary: "Dictionary attack", bruteforce: "Brute-force attack" };

let _ownTimer = null;
let _ownT0 = 0;
let _ownController = null;

function fmtElapsed(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds - m * 60;
  return m > 0 ? `${m}:${String(Math.floor(s)).padStart(2, "0")}` : `${seconds.toFixed(1)}s`;
}

function ownElapsed() {
  return (performance.now() - _ownT0) / 1000;
}

function startOwnTimer(label) {
  const el = $("own-timer");
  _ownT0 = performance.now();
  const tick = () => { el.textContent = `⏱ ${label} running… ${fmtElapsed(ownElapsed())}`; };
  tick();
  el.style.display = "block";
  _ownTimer = setInterval(tick, 100);
}

function stopOwnTimer() {
  if (_ownTimer) { clearInterval(_ownTimer); _ownTimer = null; }
  $("own-timer").style.display = "none";
}

async function attackOwn(mode) {
  const pw = $("own").value;
  if (!pw) {
    $("own-error").style.display = "block";
    $("own-result").style.display = "none";
    return;
  }
  $("own-error").style.display = "none";
  const btn = $(ATTACK_BTN[mode]);
  const label = ATTACK_LABEL[mode];
  const buttons = [$("attack-dict"), $("attack-brute")];
  buttons.forEach(b => b.disabled = true);
  btn.textContent = "Attacking…";
  $("own-result").style.display = "none";
  _ownController = new AbortController();
  $("attack-stop").style.display = "inline-block";
  startOwnTimer(label);
  try {
    const resp = await fetch("/api/attack_one", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({password: pw, mode: mode}),
      signal: _ownController.signal,
    });
    if (!resp.ok) { $("own-result").style.display = "none"; return; }
    const d = await resp.json();
    const [pbg, pfg] = PILL[d.rating] || ["#15202A", "#E6F1F5"];
    const col = d.cracked ? "#FF5470" : "#39FF88";
    const foundCell = d.cracked
      ? `<div><div class="ent-label">Found as</div><div class="mono" style="font-size:16px">${escapeHtml(d.found_as)}</div></div>`
      : "";
    const methodCell = d.cracked && d.method
      ? `<div><div class="ent-label">Cracked by</div><div class="mono">${escapeHtml(d.method)}</div></div>`
      : "";
    $("own-result").innerHTML = `
      <div style="display:flex; flex-wrap:wrap; gap:28px; align-items:center; margin-top:14px; padding-top:14px; border-top:1px solid var(--line)">
        <div><div class="ent-label">Attack</div><div class="mono">${label}</div></div>
        <div><div class="ent-label">Result</div><div style="font-size:22px; font-weight:600; color:${col}">${d.cracked ? "✓ Cracked" : "✗ Not cracked"}</div></div>
        <div><div class="ent-label">Tool rating</div><div><span class="pill" style="background:${pbg}; color:${pfg}; font-size:13px">${d.rating}</span> <span class="mono muted">${d.score}/100</span></div></div>
        <div><div class="ent-label">Guesses tried</div><div class="mono">${Number(d.attempts).toLocaleString()}</div></div>
        <div><div class="ent-label">Time</div><div class="mono">${d.seconds}s</div></div>
        ${methodCell}
        ${foundCell}
      </div>
      <div style="margin-top:14px; display:flex; flex-direction:column; gap:6px; font-size:13px">
        <div><span class="ent-label">Salt (8 chars, like the database):</span> <span class="mono" style="color:var(--accent-hi)">${escapeHtml(d.salt)}</span></div>
        <div style="word-break:break-all"><span class="ent-label">Stored hash = SHA-256(password + salt):</span> <span class="mono" style="color:var(--accent-hi)">${escapeHtml(d.hash)}</span></div>
      </div>`;
    $("own-result").style.display = "block";
  } catch (e) {
    if (e.name === "AbortError") {
      $("own-result").innerHTML = `<p class="hint" style="margin-top:14px; color:var(--muted)">⏹ ${label} stopped after ${fmtElapsed(ownElapsed())}.</p>`;
      $("own-result").style.display = "block";
    } else {
      $("own-result").style.display = "none";
    }
  } finally {
    stopOwnTimer();
    $("attack-stop").style.display = "none";
    _ownController = null;
    buttons.forEach(b => b.disabled = false);
    btn.textContent = label;
  }
}

function stopOwnAttack() {
  if (_ownController) { _ownController.abort(); }
}

document.addEventListener("DOMContentLoaded", () => {
  $("status").style.display = "none";   // always start hidden, even on a cached page
  $("run").addEventListener("click", () => run("run"));
  $("count").addEventListener("change", clampCount);
  $("attack-dict").addEventListener("click", () => attackOwn("dictionary"));
  $("attack-brute").addEventListener("click", () => attackOwn("bruteforce"));
  $("attack-stop").addEventListener("click", stopOwnAttack);
  $("own").addEventListener("keydown", (e) => { if (e.key === "Enter") attackOwn("dictionary"); });
  $("own").addEventListener("input", () => { $("own-error").style.display = "none"; });
});
