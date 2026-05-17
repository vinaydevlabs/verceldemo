import os, json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

def mean(values):
    return sum(values) / len(values)

def p95(values):
    sorted_vals = sorted(values)
    index = int(0.95 * len(sorted_vals))
    return sorted_vals[min(index, len(sorted_vals) - 1)]

@app.get("/api/analytics")
def health():
    return {"status": "ok"}

@app.post("/api/analytics")
def analytics(req: AnalyticsRequest):
    result = {}
    for region in req.regions:
        records = [r for r in RAW_DATA if r["region"] == region]
        if not records:
            result[region] = None
            continue
        latencies = [r["latency_ms"] for r in records]
        uptimes   = [r["uptime_pct"] for r in records]
        result[region] = {
            "avg_latency": round(mean(latencies), 4),
            "p95_latency": round(p95(latencies), 4),
            "avg_uptime":  round(mean(uptimes), 4),
            "breaches":    sum(1 for l in latencies if l > req.threshold_ms),
        }
    return result