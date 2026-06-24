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
["narrative", "top-ugc", "giftees", "highlights"].forEach(id =>
  document.addEventListener("input", e => { if (e.target.id === id) render(); }));

function render() {
  if (!current) return;
  const d = current;
  const L = [];
  L.push($("narrative").value.trim());
  L.push("");
  L.push(`${d.month_name} UGC:`);
  L.push(`• Organic Outreach: ${d.outreach.toLocaleString()}`);
  L.push(`• Gifts Confirmed: ${d.gifts.toLocaleString()}`);
  L.push(`• ${d.month_name} UGC: ${d.ugc_count.toLocaleString()}`);
  L.push(`• ${d.month_name} EMV: $${d.emv.toLocaleString()}`);
  L.push("");
  if (d.top_posts.length) {
    L.push("Top performing content:");
    d.top_posts.forEach(p => L.push(`• @${p.handle} — $${Math.round(p.emv).toLocaleString()} — ${p.url}`));
    L.push("");
  }
  const ugc = $("top-ugc").value.trim();
  const gift = $("giftees").value.trim();
  L.push(`Top UGC of the week: ${ugc || "[fill in]"}`);
  L.push(`Top Giftees of the week: ${gift || "[fill in]"}`);
  const hi = $("highlights").value.trim();
  if (hi) { L.push(""); L.push(hi); }
  L.push("");
  L.push("As always, let us know if you have any questions!");
  $("preview").textContent = L.join("\n");
}

$("copy").addEventListener("click", () => {
  navigator.clipboard.writeText($("preview").textContent).then(() => {
    const b = $("copy"); const t = b.textContent;
    b.textContent = "Copied ✓";
    setTimeout(() => b.textContent = t, 1500);
  });
});

function setStatus(msg, isError) {
  const s = $("status");
  s.textContent = msg;
  s.classList.toggle("error", !!isError);
}
