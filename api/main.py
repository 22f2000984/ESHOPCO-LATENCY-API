import json
import statistics
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry.json safely (Vercel-compatible path)
BASE_DIR = Path(__file__).resolve().parent.parent
telemetry_path = BASE_DIR / "telemetry.json"

raw = telemetry_path.read_text().strip()
telemetry = json.loads(raw)

@app.post("/")
async def metrics(request: Request):
    body = await request.json()
    regions: List[str] = body["regions"]
    threshold = body["threshold_ms"]

    response = {}

    for region in regions:
        records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        response[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": sorted(latencies)[int(0.95 * (len(latencies) - 1))],
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(1 for l in latencies if l > threshold),
        }

    return response
