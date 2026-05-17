# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import numpy as np

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load the telemetry data once when the function starts
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/api/analytics")
def analytics(req: AnalyticsRequest):
    result = {}

    for region in req.regions:
        # Get all records for this region
        records = [r for r in RAW_DATA if r["region"] == region]

        if not records:
            result[region] = None
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes   = [r["uptime"] for r in records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(np.percentile(latencies, 95)), 4),
            "avg_uptime":  round(float(np.mean(uptimes)), 4),
            "breaches":    int(sum(1 for l in latencies if l > req.threshold_ms)),
        }

    return result