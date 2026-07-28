"""
Agency 8 Newsletter Tool — web app (Phase 2).

A small FastAPI service that wraps the engine so coworkers can pick a client,
generate the draft in the browser, edit it, and copy it out.

Run locally:   uvicorn app:app --reload --port 8000
Then open:     http://localhost:8000
"""

import os
import calendar
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import newsletter as nl

app = FastAPI(title="Agency 8 Newsletter Tool")

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

# Optional shared access password — set APP_PASSWORD in the environment to require it.
APP_PASSWORD = os.environ.get("APP_PASSWORD")


def check_auth(provided):
    if APP_PASSWORD and provided != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Wrong or missing password.")


class ClientRequest(BaseModel):
    client: str
    password: str | None = None


class GenerateRequest(BaseModel):
    client: str
    month: str | None = None   # "YYYY-MM"; defaults to current month
    password: str | None = None
    top_period: str = "month"       # "month" or "week" — scope for Top UGC / Top Giftees only
    week_start: str | None = None   # "YYYY-MM-DD", required when top_period == "week"
    week_end: str | None = None     # "YYYY-MM-DD", required when top_period == "week"


@app.get("/api/clients")
def clients():
    return {"clients": [{"key": k, "name": v["display_name"]} for k, v in config.CLIENTS.items()],
            "auth_required": bool(APP_PASSWORD)}


@app.post("/api/months")
def months(req: ClientRequest):
    check_auth(req.password)
    if req.client not in config.CLIENTS:
        raise HTTPException(status_code=404, detail="Unknown client.")
    client_cfg = config.CLIENTS[req.client]
    ws_id = client_cfg.get("archive_workspace")
    if not ws_id:
        return {"months": nl.recent_months(12)}   # no Archive → offer recent months
    token = client_cfg.get("archive_token") or nl.archive_token()
    return {"months": nl.ugc_campaign_months(ws_id, token)}


@app.post("/api/generate")
def generate(req: GenerateRequest):
    check_auth(req.password)
    if req.client not in config.CLIENTS:
        raise HTTPException(status_code=404, detail="Unknown client.")
    client = config.CLIENTS[req.client]

    if req.month:
        year, month = map(int, req.month.split("-"))
    else:
        now = datetime.utcnow()
        year, month = now.year, now.month

    if req.top_period == "week":
        if not (req.week_start and req.week_end):
            raise HTTPException(status_code=400, detail="Pick a start and end date for the week.")
        if req.week_end < req.week_start:
            raise HTTPException(status_code=400, detail="Week end date must be on or after the start date.")

    token = client.get("archive_token") or nl.archive_token()
    gc = nl.get_gspread()
    nums = nl.compute_numbers(client, year, month, token, gc,
                              top_period=req.top_period,
                              week_start=req.week_start, week_end=req.week_end)
    narrative = nl.generate_narrative(client["display_name"], calendar.month_name[month],
                                      nums, nl._env("ANTHROPIC_API_KEY"))

    cid = nums.get("campaign_id")
    return {
        "client": client["display_name"],
        "month_name": calendar.month_name[month],
        "year": year,
        "campaign_name": nums["campaign_name"],
        "campaign_url": f"https://app.archive.com/crm/p/c/{cid}" if cid else "",
        "outreach": nums["outreach"],
        "gifts": nums["gifts"],
        "ugc_count": nums["ugc_count"],
        "emv": round(nums["emv"]),
        "impressions": nums.get("impressions", 0),
        "followership": nums.get("followership", 0),
        "narrative": narrative or "",
        "top_ugc": nums["top_posts"],           # up to TOP_POSTS candidates [{handle, emv, url}]
        "top_giftees": nums.get("top_giftees", []),  # up to 10 candidates [{handle, followers}]
        "top_period": req.top_period,
        "week_start": req.week_start,
        "week_end": req.week_end,
    }


# Serve the frontend. html=True makes "/" return index.html.
# Mounted last so the /api/* routes above always take precedence.
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
