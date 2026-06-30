// Agency 8 Newsletter Tool — frontend

let current = null;  // last generated data

const $ = (id) => document.getElementById(id);
let authRequired = false;

// Load clients into the dropdown, then load the first client's available months
fetch("/api/clients").then(r => r.json()).then(data => {
  const sel = $("client");
  data.clients.forEach(c => {
    const o = document.createElement("option");
    o.value = c.key; o.textContent = c.name;
    sel.appendChild(o);
  });
  authRequired = data.auth_required;
  if (authRequired) $("pw-fld").style.display = "flex";
  loadMonths();
});

// Reload available months whenever the client (or password) changes
$("client").addEventListener("change", loadMonths);
$("password").addEventListener("change", () => { if (authRequired) loadMonths(); });
$("generate").addEventListener("click", generate);

async function loadMonths() {
  const sel = $("month");
  sel.innerHTML = '<option value="">Loading months…</option>';
  $("generate").disabled = true;
  try {
    const r = await fetch("/api/months", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client: $("client").value, password: $("password").value || null }),
    });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      throw new Error(e.detail || `Error ${r.status}`);
    }
    const data = await r.json();
    if (!data.months.length) {
      sel.innerHTML = '<option value="">No UGC campaigns found</option>';
      return;
    }
    sel.innerHTML = data.months.map(m => `<option value="${m.value}">${m.label}</option>`).join("");
    $("generate").disabled = false;
    setStatus("");
  } catch (e) {
    sel.innerHTML = '<option value="">—</option>';
    setStatus(authRequired ? "Enter the team password, then pick a client." : e.message, true);
  }
}

async function generate() {
  const btn = $("generate");
  btn.disabled = true;
  setStatus("Pulling numbers and drafting copy… (this can take 10–20s)");
  try {
    const r = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client: $("client").value,
        month: $("month").value,
        password: $("password").value || null,
      }),
    });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      throw new Error(e.detail || `Error ${r.status}`);
    }
    current = await r.json();
    populate(current);
    setStatus("");
    $("workspace").classList.remove("hidden");
  } catch (e) {
    setStatus(e.message, true);
  } finally {
    btn.disabled = false;
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const nl2br = (s) => esc(s).replace(/\n/g, "<br>");

// ── Metric dropdown ───────────────────────────────────────────────────────────
document.addEventListener("click", e => {
  const menu = $("metric-dropdown-menu");
  if (!menu) return;
  if ($("metric-dropdown-btn") && $("metric-dropdown-btn").contains(e.target)) {
    menu.classList.toggle("hidden");
  } else if (!menu.contains(e.target)) {
    menu.classList.add("hidden");
  }
});

function updateDropdownLabel() {
  const all = [...document.querySelectorAll(".m-toggle")];
  const n = all.filter(c => c.checked).length;
  const btn = $("metric-dropdown-btn");
  if (btn) btn.textContent = n === all.length ? "▾ All metrics selected"
    : n === 0 ? "▾ No metrics selected"
    : `▾ ${n} of ${all.length} metrics selected`;
}

// ── Pick-list helpers ─────────────────────────────────────────────────────────
function buildPickList(containerId, items, preselect) {
  const wrap = $(containerId);
  if (!wrap) return;
  wrap.innerHTML = items.map((it, i) => `
    <label class="pick-item${i < preselect ? " checked" : ""}" data-idx="${i}">
      <input type="checkbox" class="pick-chk" ${i < preselect ? "checked" : ""}>
      <span class="pick-handle">@${esc(it.handle)}</span>
      <span class="pick-meta">${it.meta || ""}</span>
      ${it.url ? `<a href="${esc(it.url)}" target="_blank" rel="noopener">View ↗</a>` : ""}
    </label>`).join("");
  wrap.querySelectorAll(".pick-chk").forEach(cb => {
    cb.addEventListener("change", () => {
      const checked = [...wrap.querySelectorAll(".pick-chk:checked")];
      if (checked.length > preselect) { cb.checked = false; return; }
      wrap.querySelectorAll(".pick-item").forEach(li =>
        li.classList.toggle("checked", li.querySelector(".pick-chk").checked));
      render();
    });
  });
}

function getPickedItems(containerId) {
  const wrap = $(containerId);
  if (!wrap) return [];
  return [...wrap.querySelectorAll(".pick-chk:checked")].map(cb => {
    const li = cb.closest(".pick-item");
    return {
      handle: li.querySelector(".pick-handle").textContent.replace(/^@/, ""),
      url:    li.querySelector("a") ? li.querySelector("a").getAttribute("href") : "",
    };
  });
}

// ── Populate after generate ───────────────────────────────────────────────────
function populate(d) {
  $("narrative").value = d.narrative;

  // Numbers grid (all 6 metrics always shown in the grid)
  $("metrics").innerHTML = [
    ["Organic Outreach",   d.outreach.toLocaleString()],
    ["Gifts Confirmed",    d.gifts.toLocaleString()],
    [`${d.month_name} UGC`, d.ugc_count.toLocaleString()],
    [`${d.month_name} EMV`, "$" + d.emv.toLocaleString()],
    ["Impressions",        d.impressions ? d.impressions.toLocaleString() : "—"],
    ["Total Followership", d.followership ? d.followership.toLocaleString() : "—"],
  ].map(([l, v]) => `<div class="metric"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");

  // Reset metric toggles — outreach/gifts/ugc/emv on by default
  document.querySelectorAll(".m-toggle").forEach(c => {
    c.checked = ["outreach","gifts","ugc","emv"].includes(c.value);
  });
  updateDropdownLabel();

  // Top UGC pick-list — up to TOP_POSTS candidates, first 3 pre-selected
  buildPickList("top-ugc-list",
    (d.top_ugc || []).map(p => ({
      handle: p.handle,
      meta: p.emv ? `$${Math.round(p.emv).toLocaleString()} EMV` : "",
      url: p.url,
    })), 3);

  // Top Giftees pick-list — up to 10 by followers, first 3 pre-selected
  buildPickList("giftees-list",
    (d.top_giftees || []).map(g => ({
      handle: g.handle || g,
      meta: g.followers ? `${Number(g.followers).toLocaleString()} followers` : "",
      url: `https://www.instagram.com/${esc((g.handle || g).replace(/^@/, ""))}/`,
    })), 3);

  if (!d.campaign_name) {
    setStatus("⚠ No monthly UGC campaign found for this month — UGC/EMV show 0.", true);
  }
  render();
}

// Re-render whenever narrative, highlights, or metric toggles change
document.addEventListener("input",  e => {
  if (e.target.id === "narrative" || e.target.id === "highlights") render();
});
document.addEventListener("change", e => {
  if (e.target.classList.contains("m-toggle")) { updateDropdownLabel(); render(); }
});

// ── Build HTML (preview + copy) ───────────────────────────────────────────────
function buildHtml() {
  const d = current;
  const head = d.month_name + " UGC";  // campaign link removed (CRM URL requires login)
  const show = id => { const c = document.querySelector(`.m-toggle[value="${id}"]`); return !c || c.checked; };

  let h = `<p>${nl2br($("narrative").value.trim())}</p>`;
  h += `<p><b>${head}</b></p><ul>`;
  if (show("outreach")) h += `<li>Organic Outreach: ${d.outreach.toLocaleString()}</li>`;
  if (show("gifts"))    h += `<li>Gifts Confirmed: ${d.gifts.toLocaleString()}</li>`;
  if (show("ugc"))      h += `<li>${d.month_name} UGC: ${d.ugc_count.toLocaleString()}</li>`;
  if (show("emv"))      h += `<li>${d.month_name} EMV: $${d.emv.toLocaleString()}</li>`;
  if (show("impressions") && d.impressions)
    h += `<li>Impressions: ${d.impressions.toLocaleString()}</li>`;
  if (show("followership") && d.followership)
    h += `<li>Total Followership: ${d.followership.toLocaleString()}</li>`;

  // Top UGC — from the checklist selections
  const ugcPicked = getPickedItems("top-ugc-list");
  if (ugcPicked.length) {
    h += `<li>Top UGC of the week:<ul>`;
    ugcPicked.forEach(p => {
      h += p.url
        ? `<li><a href="${esc(p.url)}">@${esc(p.handle)}</a></li>`
        : `<li>@${esc(p.handle)}</li>`;
    });
    h += `</ul></li>`;
  }

  // Top Giftees — from the checklist selections (links to Instagram)
  const giftPicked = getPickedItems("giftees-list");
  if (giftPicked.length) {
    h += `<li>Top Giftees of the week:<ul>`;
    giftPicked.forEach(g => {
      const handle = g.handle.replace(/^@/, "");
      h += `<li><a href="https://www.instagram.com/${esc(handle)}/">@${esc(handle)}</a></li>`;
    });
    h += `</ul></li>`;
  }

  h += `</ul>`;
  const hi = $("highlights") ? $("highlights").value.trim() : "";
  if (hi) h += `<p>${nl2br(hi)}</p>`;
  h += `<p>As always, let us know if you have any questions!</p>`;
  return h;
}

function render() {
  if (!current) return;
  $("preview").innerHTML = buildHtml();
}

$("copy").addEventListener("click", async () => {
  const b = $("copy"), label = b.textContent;
  const html = buildHtml();
  const plain = $("preview").innerText;
  try {
    await navigator.clipboard.write([new ClipboardItem({
      "text/html":  new Blob([html],  { type: "text/html" }),
      "text/plain": new Blob([plain], { type: "text/plain" }),
    })]);
  } catch (e) {
    await navigator.clipboard.writeText(plain);
  }
  b.textContent = "Copied ✓";
  setTimeout(() => (b.textContent = label), 1500);
});

function setStatus(msg, isError) {
  const s = $("status");
  s.textContent = msg;
  s.classList.toggle("error", !!isError);
}
