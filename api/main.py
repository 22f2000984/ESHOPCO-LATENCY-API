import json
import statistics
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ CORS required by grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry
with open("api/q-vercel-latency.json", "r") as f:
    DATA = json.load(f)


@app.post("/")
async def metrics(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    regions = body.get("regions")
    threshold = body.get("threshold_ms")

    if not regions or threshold is None:
        raise HTTPException(status_code=400, detail="Missing fields")

    result = {}

    for region in regions:
        rows = [r for r in DATA if r["region"] == region]
        lat = [r["latency_ms"] for r in rows]
        up = [r["uptime"] for r in rows]

        result[region] = {
            "avg_latency": round(statistics.mean(lat), 2),
            "p95_latency": round(statistics.quantiles(lat, n=100)[94], 2),
            "avg_uptime": round(statistics.mean(up), 4),
            "breaches": sum(1 for x in lat if x > threshold),
        }

    return result
