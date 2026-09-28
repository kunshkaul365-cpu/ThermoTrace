from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from fusion import get_fused_assessment, get_diverse_assessments, get_all_map_sources, get_stats, get_frp_history

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/thermal-sources")
def get_thermal_sources():
    return get_all_map_sources()

@app.get("/api/assessments/{source_id}")
def get_single_assessment(source_id: str):
    result = get_fused_assessment(source_id)
    if "error" in result:
         raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/assessments/{source_id}/frp-history")
def get_source_frp_history(source_id: str, days: int = 30):
    return get_frp_history(source_id, days=days)

@app.get("/api/assessments")
def get_assessments():
    return get_diverse_assessments(limit=200)

@app.get("/api/stats")
def get_dashboard_stats():
    return get_stats()