import json
import statistics
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# ---------- FORCE CORS FOR *ALL* REQUESTS ----------
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    # Handle OPTIONS early (preflight)
    if request.method == "OPTIONS":
        response = JSONResponse(content={}, status_code=200)
    else:
        response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response
# --------------------------------------------------

# Load telemetry.json
BASE_DIR = Path(__file__).resolve().parent.parent
telemetry = json.loads((BASE_DIR / "telemetry.json").read_text())

# GET handler (for probes / browser)
@app.get("/")
async def health():
    return {"ok": True}

# POST handler (graded endpoint)
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

    return result
