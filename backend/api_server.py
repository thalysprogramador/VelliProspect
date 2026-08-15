
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database as db
import scraper
import ai_evaluator
import time

app = FastAPI(title="Velli Prospect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    niche: str
    region: str
    source: str
    criteria: str = ""
    min_score: int = 7
    max_results: int = 50
    block_large_portals: bool = True

class SettingsRequest(BaseModel):
    key: str
    value: str

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Velli Prospect Backend"}

@app.get("/api/campaigns")
def get_campaigns():
    return db.get_all_campaigns()

@app.get("/api/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    return db.get_campaign(campaign_id)

@app.get("/api/campaigns/{campaign_id}/leads")
def get_leads(campaign_id: str):
    return db.get_leads_by_campaign(campaign_id)

@app.delete("/api/campaigns/{campaign_id}")
def delete_campaign(campaign_id: str):
    db.delete_campaign(campaign_id)
    return {"status": "deleted"}

@app.get("/api/settings/{key}")
def get_setting(key: str):
    val = db.get_setting(key)
    return {"key": key, "value": val}

@app.post("/api/settings")
def set_setting(req: SettingsRequest):
    db.set_setting(req.key, req.value)
    return {"status": "saved"}

@app.post("/api/campaigns")
def create_campaign(req: ScrapeRequest, background_tasks: BackgroundTasks):
    # This simulates the Flet workflow but asynchronous
    camp_name = f"{req.niche} em {req.region}"
    cid = db.create_campaign(camp_name, req.niche, req.region, req.source, req.criteria, req.min_score, req.max_results)
    if not cid:
        raise HTTPException(status_code=500, detail="Error creating campaign")
    
    # Run scraping in background
    background_tasks.add_task(run_scrape_task, cid, req)
    return {"status": "started", "campaign": {"id": cid}}

def run_scrape_task(campaign_id: str, req: ScrapeRequest):
    leads = scraper.scrape_leads(
        req.niche, req.region, req.source, 
        req.max_results, req.block_large_portals
    )
    if not leads:
        db.update_campaign_stats(campaign_id, status="completed")
        return
        
    db.update_campaign_stats(campaign_id, total_found=len(leads))
    
    api_key = db.get_setting("gemini_api_key", "")
    for lead in leads:
        try:
            evaluated = ai_evaluator.evaluate_lead(lead, api_key)
            if evaluated and evaluated.get("score", 0) >= req.min_score:
                db.insert_lead(campaign_id, evaluated)
        except Exception as e:
            print(f"Error evaluating lead: {e}")
            
    db.update_campaign_stats(campaign_id, status="completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


