from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics
from pathlib import Path

app = FastAPI()

# ✅ CORS (grader requirement)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"

@app.post("/")
async def latency_metrics(request: Request):
    body = await request.json()

    regions = body.get("regions")
    threshold = body.get("threshold_ms")

    if not regions or threshold is None:
        raise HTTPException(status_code=400, detail="Invalid input")

    with open(DATA_PATH) as f:
        data = json.load(f)

    response = {}

    for region in regions:
        records = [r for r in data if r["region"] == region]

        if not records:
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime"] for r in records]

        response[region] = {
            "avg_latency": round(statistics.mean(latencies), 2),
            "p95_latency": round(statistics.quantiles(latencies, n=20)[18], 2),
            "avg_uptime": round(statistics.mean(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > threshold)
        }

    return response
