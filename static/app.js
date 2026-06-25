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

function populate(d) {
  $("narrative").value = d.narrative;
  $("metrics").innerHTML = [
    ["Organic Outreach", d.outreach.toLocaleString()],
    ["Gifts Confirmed", d.gifts.toLocaleString()],
    [`${d.month_name} UGC`, d.ugc_count.toLocaleString()],
    [`${d.month_name} EMV`, "$" + d.emv.toLocaleString()],
  ].map(([l, v]) => `<div class="metric"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  if (!d.campaign_name) {
    setStatus("⚠ No monthly UGC campaign found for this month — UGC/EMV show 0.", true);
  }
  render();
}

// Re-render the preview whenever an editable field changes
["narrative", "highlights"].forEach(id =>
  document.addEventListener("input", e => { if (e.target.id === id) render(); }));

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const nl2br = (s) => esc(s).replace(/\n/g, "<br>");

// Build the newsletter as HTML (with real hyperlinks) — used for both the preview and copy.
function buildHtml() {
  const d = current;
  const head = d.campaign_url
    ? `<a href="${d.campaign_url}">${d.month_name} UGC</a>`
    : `${d.month_name} UGC`;
  let h = `<p>${nl2br($("narrative").value.trim())}</p>`;
  h += `<p><b>${head}</b></p><ul>`;
  h += `<li>Organic Outreach: ${d.outreach.toLocaleString()}</li>`;
  h += `<li>Gifts Confirmed: ${d.gifts.toLocaleString()}</li>`;
  h += `<li>${d.month_name} UGC: ${d.ugc_count.toLocaleString()}</li>`;
  h += `<li>${d.month_name} EMV: $${d.emv.toLocaleString()}</li>`;
  if (d.top_ugc && d.top_ugc.length) {
    h += `<li>Top UGC of the week:<ul>`;
    d.top_ugc.forEach(p => h += `<li><a href="${esc(p.url)}">@${esc(p.handle)}</a></li>`);
    h += `</ul></li>`;
  }
  if (d.top_giftees && d.top_giftees.length) {
    h += `<li>Top Giftees of the week:<ul>`;
    d.top_giftees.forEach(g => h += `<li><a href="https://www.instagram.com/${esc(g)}/">@${esc(g)}</a></li>`);
    h += `</ul></li>`;
  }
  h += `</ul>`;
  const hi = $("highlights").value.trim();
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
      "text/html": new Blob([html], { type: "text/html" }),
      "text/plain": new Blob([plain], { type: "text/plain" }),
    })]);
  } catch (e) {
    await navigator.clipboard.writeText(plain);  // fallback: plain text
  }
  b.textContent = "Copied ✓";
  setTimeout(() => (b.textContent = label), 1500);
});

function setStatus(msg, isError) {
  const s = $("status");
  s.textContent = msg;
  s.classList.toggle("error", !!isError);
}
