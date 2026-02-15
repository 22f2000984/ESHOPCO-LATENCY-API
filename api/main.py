import json
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from statistics import mean

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    telemetry = json.load(f)

@app.post("/api")
async def latency_metrics(request: Request):
    body = await request.json()
    regions = body["regions"]
    threshold = body["threshold_ms"]

    response = {}

    for region in regions:
        rows = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime"] for r in rows]

        p95 = sorted(latencies)[int(0.95 * len(latencies)) - 1]

        response[region] = {
            "avg_latency": round(mean(latencies), 2),
            "p95_latency": round(p95, 2),
            "avg_uptime": round(mean(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > threshold),
        }

    return response