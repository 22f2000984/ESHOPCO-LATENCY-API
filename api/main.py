import json
import statistics
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data safely
BASE_DIR = Path(__file__).resolve().parent.parent
telemetry_path = BASE_DIR / "telemetry.json"

if not telemetry_path.exists():
    raise RuntimeError("telemetry.json not found")

telemetry = json.loads(telemetry_path.read_text())

# Optional GET handler to avoid 500 on browser / probes
@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/")
async def metrics(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    regions: List[str] = body.get("regions")
    threshold = body.get("threshold_ms")

    if not regions or threshold is None:
        raise HTTPException(status_code=400, detail="Missing regions or threshold_ms")

    result = {}

    for region in regions:
        records = [r for r in telemetry if r["region"] == region]

        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": sorted(latencies)[int(0.95 * (len(latencies) - 1))],
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(1 for l in latencies if l > threshold),
        }

    return result
