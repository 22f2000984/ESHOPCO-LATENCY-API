import json
import statistics
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

# --------- HARD CORS GUARANTEE ----------
@app.options("/")
def cors_preflight():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )
# ---------------------------------------

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# Load telemetry
BASE_DIR = Path(__file__).resolve().parent.parent
telemetry = json.loads((BASE_DIR / "telemetry.json").read_text())

@app.get("/")
def health():
    return {"ok": True}

@app.post("/")
async def metrics(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}

    regions: List[str] = body.get("regions")
    threshold = body.get("threshold_ms")

    if not regions or threshold is None:
        return {"ok": True}

    result = {}
    for region in regions:
        records = [r for r in telemetry if r["region"] == region]
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": sorted(latencies)[int(0.95 * (len(latencies) - 1))],
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(1 for l in latencies if l > threshold),
        }

    return JSONResponse(
        content=result,
        headers={"Access-Control-Allow-Origin": "*"},
    )
