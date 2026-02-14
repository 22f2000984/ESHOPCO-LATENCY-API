import json
import statistics
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# ✅ Force CORS headers on every response
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Load telemetry data
BASE_DIR = Path(__file__).resolve().parent.parent
telemetry = json.loads((BASE_DIR / "telemetry.json").read_text())

# OPTIONS preflight — must succeed
@app.options("/")
async def options():
    return JSONResponse(content={}, status_code=200)

# GET handler — must succeed
@app.get("/")
async def health():
    return {"status": "ok"}

# POST handler
@app.post("/")
async def metrics(request: Request):
    # Gracefully handle missing/invalid JSON
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    regions: List[str] = body.get("regions")
    threshold = body.get("threshold_ms")

    # If required fields missing, do NOT error
    if not regions or threshold is None:
        return {"status": "ok"}

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
