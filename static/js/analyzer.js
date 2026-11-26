"use strict";

const PILL = {
  "Very Weak": ["#3A0E16", "#FF5470"],
  "Weak":      ["#3A1E0A", "#FFB067"],
  "Fair":      ["#2E2A0A", "#FFE066"],
  "Strong":    ["#0C2E1F", "#39FF88"],
  "Very Strong": ["#06262E", "#5CE1FF"],
};
const BAR = {
  "Very Weak": "#FF5470", "Weak": "#FF8A3D", "Fair": "#FFD23F",
  "Strong": "#39FF88", "Very Strong": "#5CE1FF",
};

const $ = (id) => document.getElementById(id);

function render(d) {
  $("score").textContent = d.score;
  const rating = $("rating");
  rating.textContent = d.rating;
  const [bg, fg] = PILL[d.rating] || ["#15202A", "#E6F1F5"];
  rating.style.background = bg; rating.style.color = fg;
  $("meta").textContent = `${d.length} chars · ${d.classes} classes · ${d.elapsed_ms} ms`;

  const sb = $("score-bar");
  sb.style.width = d.score + "%";
  sb.style.background = BAR[d.rating] || "#8BA3B3";

  const passed = d.policy.rules.filter(r => r.passed).length;
  $("policy-sub").textContent = `v1.0 · ${passed} of ${d.policy.rules.length} passed`;
  $("rules").innerHTML = d.policy.rules.map(r => `
    <li>
      <span class="rid">${r.id}</span>
      <span class="badge ${r.passed ? "ok" : "bad"}">${r.passed ? "✓" : "✗"}</span>
      <span class="rname">${r.name}</span>
      <span class="rdetail">${escapeHtml(r.detail)}</span>
    </li>`).join("");

  $("naive").textContent = d.entropy.naive;
  $("adjusted").textContent = d.entropy.adjusted;
  $("pool").textContent = `character pool N = ${d.entropy.pool}`;
  const maxBits = Math.max(d.entropy.naive, 1);
  $("naive-bar").style.width = "100%";
  $("adj-bar").style.width = Math.round((d.entropy.adjusted / maxBits) * 100) + "%";

  $("crack").innerHTML = d.crack_times.map(t => `
    <tr>
      <td class="mono">${t.id}</td>
      <td>${t.label}</td>
      <td class="right mono" style="font-weight:600">${t.human}</td>
    </tr>`).join("");

  $("tips").innerHTML = (d.recommendations.length ? d.recommendations : ["Looks solid. No changes needed."])
    .map(t => `<li>${escapeHtml(t)}</li>`).join("");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => (
    {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]
  ));
}

async function analyze() {
  const pw = $("pw").value;
  if (!pw) return;
  try {
    const resp = await fetch("/api/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({password: pw}),
    });
    if (!resp.ok) return;
    render(await resp.json());
  } catch (e) { /* ignore transient errors */ }
}

let timer = null;
function debounced() {
  clearTimeout(timer);
  timer = setTimeout(analyze, 300);
}

document.addEventListener("DOMContentLoaded", () => {
  $("analyze").addEventListener("click", analyze);
  $("pw").addEventListener("input", debounced);
  $("toggle").addEventListener("click", () => {
    const i = $("pw");
    i.type = i.type === "password" ? "text" : "password";
  });
  analyze();
});
