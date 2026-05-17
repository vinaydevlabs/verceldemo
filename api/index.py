import os, json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# More robust path — works both locally and on Vercel
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/api/analytics")
def analytics(req: AnalyticsRequest):
    result = {}
    for region in req.regions:
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