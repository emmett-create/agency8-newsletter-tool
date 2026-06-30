"""
Agency 8 Newsletter Tool — engine (Phase 1).

Pulls a client's monthly numbers from Google Sheets (outreach, gifts) and the
Archive API (UGC count, EMV, top posts), then prints an editable newsletter draft.

Usage:
    python newsletter.py snif            # current month
    python newsletter.py snif 2026-06    # a specific month
"""

import os
import re
import sys
import json
import calendar
from datetime import datetime, timedelta

import requests
import gspread

import config


# ── token ─────────────────────────────────────────────────────────────────────
def _env(name):
    """Read a secret: OS environment first (Render), then ~/.env.shared (local)."""
    if os.environ.get(name):
        return os.environ[name]
    path = os.path.expanduser("~/.env.shared")
    try:
        with open(path) as f:
            for line in f:
                if line.strip().startswith(name + "="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return None


def archive_token():
    tok = _env("ARCHIVE_APP_TOKEN")
    if not tok:
        raise SystemExit("ARCHIVE_APP_TOKEN not found in ~/.env.shared")
    return tok


def get_gspread():
    """gspread client from GOOGLE_CREDENTIALS_JSON env (Render) or the creds file (local)."""
    raw = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if raw:
        return gspread.service_account_from_dict(json.loads(raw))
    return gspread.service_account(filename=config.GOOGLE_CREDENTIALS)


def compute_numbers(client, year, month, token, gc):
    """All the data for one client/month — shared by the CLI and the web app."""
    sh = gc.open_by_key(client["report_sheet_key"])
    forms = reporting_formulas(sh)
    outreach = count_outreach(sh, forms.get("outreach"), year, month, client)
    gifts, top_giftees = gift_data(gc, client, sh, forms.get("form responses"), year, month)

    ws_id = client.get("archive_workspace")
    camp = find_monthly_ugc_campaign(ws_id, token, year, month) if ws_id else None
    if camp:
        stats = campaign_stats(ws_id, token, camp["id"], config.TOP_POSTS)
        campaign_name, campaign_id = camp["name"], camp["id"]
    else:
        stats = {"ugc_count": 0, "emv": 0, "top_posts": []}
        campaign_name = campaign_id = None
    return {"month": month, "outreach": outreach, "gifts": gifts,
            "top_giftees": top_giftees, "campaign_name": campaign_name,
            "campaign_id": campaign_id, **stats}


# ── dates ───────────────────────────────────────────────────────────────────────
def parse_date(s):
    s = str(s).strip()
    if not s:
        return None
    for f in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
              "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    return None


_SHEETS_EPOCH = datetime(1899, 12, 30)  # Google Sheets day 0


def to_date(v):
    """Convert a cell to a date. Handles Sheets serial numbers (real dates, any display
    format) and text dates. Returns None for non-dates."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return _SHEETS_EPOCH + timedelta(days=float(v)) if 20000 < v < 80000 else None
    return parse_date(v)


def month_bounds(year, month):
    """Return UTC ISO strings for the first and last instant of the month."""
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01T00:00:00Z"
    end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z"
    return start, end


# ── Archive API ─────────────────────────────────────────────────────────────────
def archive_query(query, variables, workspace_id, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "WORKSPACE-ID": workspace_id,
    }
    r = requests.post(config.ARCHIVE_API_URL, headers=headers,
                      json={"query": query, "variables": variables}, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise SystemExit(f"Archive API error: {data['errors']}")
    return data["data"]


_MONTHS = {name.upper(): num for num, name in enumerate(calendar.month_name) if name}


def _campaign_month(name, created):
    """(year, month) for a campaign, read from its NAME (e.g. 'A8 June '26 UGC').
    Year: explicit '26 / 2026 in the name if present, else the creation year."""
    up = name.upper()
    month = next((num for mn, num in _MONTHS.items() if mn in up), None)
    if not month:
        return None
    m2 = re.search(r"'(\d{2})", name)
    m4 = re.search(r"20\d{2}", name)
    if m2:
        year = 2000 + int(m2.group(1))
    elif m4:
        year = int(m4.group(0))
    elif created:
        year = created.year
    else:
        return None
    return (year, month)


def _ugc_campaigns(workspace_id, token):
    """[(year, month, campaign_node)] for every 'A8 <Month> UGC' campaign."""
    q = "query { campaigns(first: 100) { nodes { id name createdAt } } }"
    nodes = archive_query(q, {}, workspace_id, token)["campaigns"]["nodes"]
    out = []
    for c in nodes:
        up = c["name"].upper()
        if "UGC" not in up or "GIFTED" in up or "TOTAL" in up:
            continue
        created = parse_date(c["createdAt"].replace("T", " ").replace("Z", ""))
        ym = _campaign_month(c["name"], created)
        if ym:
            out.append((ym[0], ym[1], c))
    return out


def find_monthly_ugc_campaign(workspace_id, token, year, month):
    """The 'A8 <Month> UGC' campaign for the given month (month read from the name)."""
    for (y, m, c) in _ugc_campaigns(workspace_id, token):
        if y == year and m == month:
            return c
    return None


def ugc_campaign_months(workspace_id, token):
    """Months (most recent first) that have a valid 'A8 <Month> UGC' campaign."""
    seen = {}
    for (y, m, c) in _ugc_campaigns(workspace_id, token):
        seen[(y, m)] = c["name"]
    return [{"value": f"{y:04d}-{m:02d}",
             "label": f"{calendar.month_name[m]} {y}",
             "campaign": seen[(y, m)]}
            for (y, m) in sorted(seen, reverse=True)]


def campaign_stats(workspace_id, token, campaign_id, top_n):
    """Total UGC count, total EMV (dollars), and the top N posts by EMV."""
    q = """
    query($cid: ID!, $after: String) {
      items(first: 100, after: $after,
            filter: { campaignsIds: [$cid] },
            sorting: { sortKey: EARNED_MEDIA_VALUE, sortOrder: DESC }) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes {
          archivePublicUrl originalUrl
          socialProfile { accountName }
          currentEngagement { earnedMediaValue }
        }
      }
    }"""
    total = 0
    emv_total = 0  # earnedMediaValue is already in dollars (verified vs Archive UI)
    top = []
    after = None
    while True:
        items = archive_query(q, {"cid": campaign_id, "after": after},
                              workspace_id, token)["items"]
        total = items["totalCount"]
        for n in items["nodes"]:
            emv_total += int(n["currentEngagement"]["earnedMediaValue"] or 0)
        if not top:  # first page is already sorted EMV-desc → holds the top posts
            for n in items["nodes"][:top_n]:
                top.append({
                    "handle": (n.get("socialProfile") or {}).get("accountName", "?"),
                    "emv": int(n["currentEngagement"]["earnedMediaValue"] or 0),
                    "url": n.get("archivePublicUrl") or n.get("originalUrl") or "",
                })
        if items["pageInfo"]["hasNextPage"]:
            after = items["pageInfo"]["endCursor"]
        else:
            break
    return {"ugc_count": total, "emv": emv_total, "top_posts": top}


# ── Google Sheets (formula-driven) ──────────────────────────────────────────────
# Each client's "Reporting" tab defines the source of truth: the Outreach box and the
# Form Responses box hold COUNTIFS formulas naming exactly which tabs+columns to count.
_REF_RE = re.compile(r"(?:'([^']+)'!|(?<![\w'])([A-Za-z0-9_]+)!)\$?([A-Z]{1,3})\$?:\$?[A-Z]{1,3}")


def _parse_refs(formula):
    """Distinct (tab, column-letter) pairs referenced by a COUNTIFS-sum formula."""
    refs = []
    for m in _REF_RE.finditer(formula or ""):
        pair = (m.group(1) or m.group(2), m.group(3))
        if pair not in refs:
            refs.append(pair)
    return refs


def _col_idx(col):
    n = 0
    for ch in col.upper():
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _to_int(s):
    digits = re.sub(r"[^0-9]", "", str(s))
    return int(digits) if digits else 0


def reporting_formulas(sh):
    """{lowercased label: formula} from the Reporting tab (col F = label, col G = formula)."""
    rep = next((w for w in sh.worksheets() if "reporting" in w.title.lower()), None)
    if not rep:
        return {}
    out = {}
    for row in rep.get("F1:G40", value_render_option="FORMULA"):
        if len(row) >= 2 and str(row[0]).strip():
            out[str(row[0]).strip().lower()] = row[1]
    return out


def count_outreach(sh, formula, year, month, client=None):
    """Sum outreach across the tabs/columns named in the 'Outreach' formula."""
    refs = _parse_refs(formula)
    if not refs and client and client.get("outreach_header"):
        # Legacy fallback (e.g. Snif): find the column by header name.
        ws = sh.worksheet(client["master_list_tab"])
        header = ws.row_values(1)
        idx = next((i for i, h in enumerate(header)
                    if h.strip().lower() == client["outreach_header"].lower()), None)
        refs = [(client["master_list_tab"], chr(65 + idx))] if idx is not None and idx < 26 else []
    titles = {w.title: w for w in sh.worksheets()}
    total = 0
    for tab, col in refs:
        ws = titles.get(tab)
        if not ws:
            continue  # referenced tab not in this spreadsheet — skip
        values = ws.col_values(_col_idx(col) + 1, value_render_option="UNFORMATTED_VALUE")[1:]
        total += sum(1 for v in values
                     if (d := to_date(v)) and d.year == year and d.month == month)
    return total


def _collect_gifts(ws, date_idx, year, month, counter, giftees):
    rows = ws.get_values(value_render_option="UNFORMATTED_VALUE")
    if not rows:
        return
    header = [str(h) for h in rows[0]]
    h_idx = next((i for i, h in enumerate(header) if "ig handle" in h.lower()), None)
    f_idx = next((i for i, h in enumerate(header) if "follower" in h.lower()), None)
    for r in rows[1:]:
        if date_idx >= len(r):
            continue
        d = to_date(r[date_idx])
        if not (d and d.year == year and d.month == month):
            continue
        counter[0] += 1
        if h_idx is not None and h_idx < len(r):
            handle = str(r[h_idx]).strip().lstrip("@")
            if handle:
                fol = _to_int(r[f_idx]) if (f_idx is not None and f_idx < len(r)) else 0
                giftees[handle] = max(giftees.get(handle, 0), fol)


def gift_data(gc, client, sh, formula, year, month):
    """(gift_count, top_3_giftee_handles). Gift tabs come from the 'Form Responses' formula,
    unless the client's gifts live in a separate spreadsheet (giftapp_sheet_key)."""
    counter = [0]
    giftees = {}
    if client.get("giftapp_sheet_key"):
        # Separate spreadsheet (e.g. Snif): match tabs by name, date always in column A.
        gsh = gc.open_by_key(client["giftapp_sheet_key"])
        extras = client.get("extra_gift_tabs", [])
        for ws in gsh.worksheets():
            t = ws.title.lower()
            if ("gift application" in t and "helper" not in t) or ws.title in extras:
                _collect_gifts(ws, 0, year, month, counter, giftees)
    else:
        titles = {w.title: w for w in sh.worksheets()}
        for tab, col in _parse_refs(formula):
            ws = titles.get(tab)
            if ws:
                _collect_gifts(ws, _col_idx(col), year, month, counter, giftees)
    top = [h for h, _ in sorted(giftees.items(), key=lambda kv: kv[1], reverse=True)[:3]]
    return counter[0], top


def recent_months(n=12):
    """Fallback month list for clients with no Archive workspace (no UGC campaigns)."""
    now = datetime.utcnow()
    y, m, out = now.year, now.month, []
    for _ in range(n):
        out.append({"value": f"{y:04d}-{m:02d}",
                    "label": f"{calendar.month_name[m]} {y}", "campaign": None})
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return out


# ── draft copy ────────────────────────────────────────────────────────────────────
INTROS = [  # fallback rotation if no API key / the call fails
    "Hi Team! Popping in with our weekly update.",
    "Happy Friday! Wanted to share a quick end-of-week pulse before the weekend.",
    "Hi Team — here's where things stand heading into the back half of the month.",
    "Hello! Sharing this week's progress and a few standouts below.",
]

# Agency 8's newsletter voice, distilled from real Born to Stand Out / Snif newsletters.
NARRATIVE_SYSTEM = """You write the opening of Agency 8's weekly client newsletter. \
Agency 8 is an influencer-marketing agency; these go to brand clients. \
Voice: warm, upbeat, concise, professional but friendly. \
Open with a short greeting (e.g. "Hi Team! Popping in with our weekly update." or \
"Happy Friday! Wanted to share a quick end-of-week pulse before the weekend.") then \
1–2 short sentences on gifting/UGC momentum and, if natural, a light forward-looking note. \
Rules: Do NOT state any specific statistics or numbers — those are listed separately below your text. \
Do NOT invent facts, launches, or names. Vary the wording from week to week. \
Output ONLY the greeting + intro sentences as plain text, no headings, no metrics, no sign-off. \
Never use em dashes or en dashes (the "—" or "–" characters) anywhere; use commas, periods, or "and" instead."""


def generate_narrative(client_name, month_name, nums, key):
    """Have Claude write the intro in Agency 8's voice. Falls back to a template on any error."""
    if not key:
        return None
    context = (f"Client: {client_name}. Month: {month_name}. "
               f"For context only (do not cite these exact figures): outreach and gifting "
               f"are active this month and UGC continues to come in. "
               f"Write this week's greeting + intro.")
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": config.DRAFT_MODEL, "max_tokens": 300, "temperature": 1.0,
                  "system": NARRATIVE_SYSTEM,
                  "messages": [{"role": "user", "content": context}]},
            timeout=40,
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"].strip()
        return re.sub(r"\s*[—–]\s*", ", ", text)   # safety net: strip any em/en dashes
    except Exception as e:
        print(f"    (auto-draft unavailable, using template: {e})")
        return None


def build_draft(client_name, month_name, year, nums, key=None):
    narrative = generate_narrative(client_name, month_name, nums, key)
    top_posts = nums.get("top_posts", [])
    top_ugc = f"@{top_posts[0]['handle']} — {top_posts[0]['url']}" if top_posts else "[fill in]"
    giftees = nums.get("top_giftees", [])
    giftees_str = ", ".join("@" + h for h in giftees) if giftees else "[fill in]"
    lines = []
    if narrative:
        lines.append(narrative)
        lines.append("")
        lines.append("[EDIT: tweak the intro above as needed.]")
    else:
        lines.append(INTROS[(year * 12 + nums["month"]) % len(INTROS)])
        lines.append("")
        lines.append("[EDIT: 1–2 sentences of narrative — gifting progress, asks, any OOO notes.]")
    lines.append("")
    lines.append(f"{month_name} UGC:")
    lines.append(f"  • Organic Outreach: {nums['outreach']}")
    lines.append(f"  • Gifts Confirmed: {nums['gifts']}")
    lines.append(f"  • {month_name} UGC: {nums['ugc_count']}")
    lines.append(f"  • {month_name} EMV: ${nums['emv']:,.0f}")
    lines.append("")
    lines.append(f"Top UGC of the week: {top_ugc}")
    lines.append(f"Top Giftees of the week: {giftees_str}")
    lines.append("")
    lines.append("As always, let us know if you have any questions!")
    return "\n".join(lines)


# ── main ────────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2 or sys.argv[1] not in config.CLIENTS:
        raise SystemExit(f"Usage: python newsletter.py <client> [YYYY-MM]\n"
                         f"Clients: {', '.join(config.CLIENTS)}")
    client = config.CLIENTS[sys.argv[1]]

    if len(sys.argv) >= 3:
        year, month = map(int, sys.argv[2].split("-"))
    else:
        now = datetime.utcnow()
        year, month = now.year, now.month
    month_name = calendar.month_name[month]

    print(f"Building {client['display_name']} newsletter for {month_name} {year}…\n")

    token = archive_token()
    gc = get_gspread()

    print("  • Pulling numbers (outreach, gifts, UGC, EMV)…")
    nums = compute_numbers(client, year, month, token, gc)
    if nums["campaign_name"]:
        print(f"    UGC campaign: {nums['campaign_name']}")
    else:
        print("    ⚠ no monthly UGC campaign found for this month")

    print("  • Drafting copy in Agency 8's voice…")
    draft = build_draft(client["display_name"], month_name, year, nums, key=_env("ANTHROPIC_API_KEY"))
    print("\n" + "=" * 64)
    print(draft)
    print("=" * 64)

    out = f"{sys.argv[1]}_{year}_{month:02d}_newsletter.txt"
    with open(out, "w") as f:
        f.write(draft)
    print(f"\nSaved draft to: {out}")


if __name__ == "__main__":
    main()
