
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database as db
import scraper
import ai_evaluator

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
    camp_name = f"{req.niche} em {req.region}"
    cid = db.create_campaign(camp_name, req.niche, req.region, req.source, req.criteria, req.min_score, req.max_results)
    if not cid:
        raise HTTPException(status_code=500, detail="Error creating campaign")
    
    background_tasks.add_task(run_scrape_task, cid, req)
    return {"status": "started", "campaign": {"id": cid}}

def run_scrape_task(campaign_id: str, req: ScrapeRequest):
    try:
        leads = scraper.scrape_leads(
            req.niche, req.region, req.source, 
            req.max_results, req.block_large_portals
        )
        if not leads:
            db.update_campaign_stats(campaign_id, status="completed")
            return
            
        db.update_campaign_stats(campaign_id, total_found=len(leads))
        
        api_key = db.get_setting("gemini_api_key", "")
        approved = 0
        discarded = 0
        
        for lead in leads:
            try:
                # Pass lead, api_key AND req.criteria
                evaluated = ai_evaluator.evaluate_lead(lead, api_key, req.criteria)
                
                score = evaluated.get("score", 5) if isinstance(evaluated, dict) else 5
                
                # Check score requirement
                if score >= req.min_score:
                    # Prepare complete lead object with proper field keys
                    lead_data = {
                        "name": lead.get("Nome") or lead.get("name") or "Lead Encontrado",
                        "link": lead.get("Link") or lead.get("link") or "",
                        "description": lead.get("Descricao (Bio/Web)") or lead.get("description") or "",
                        "has_phone": lead.get("Tem Telefone?") == "Sim" or bool(lead.get("has_phone")),
                        "has_email": lead.get("Tem E-mail?") == "Sim" or bool(lead.get("has_email")),
                        "score": score,
                        "reason": evaluated.get("reason", "Lead avaliado") if isinstance(evaluated, dict) else "Lead extraido",
                        "tags": evaluated.get("tags", []) if isinstance(evaluated, dict) else [],
                        "decision_maker": evaluated.get("decision_maker", "Proprietario") if isinstance(evaluated, dict) else "Proprietario",
                        "whatsapp_ready": evaluated.get("whatsapp_ready", True) if isinstance(evaluated, dict) else True,
                    }
                    db.insert_lead(campaign_id, lead_data)
                    approved += 1
                else:
                    discarded += 1
            except Exception as e:
                print(f"[Backend Error] Evaluation failed for lead: {e}")
                # Fallback: insert lead even if AI evaluation encounters an issue
                lead_data = {
                    "name": lead.get("Nome") or "Lead Extraído",
                    "link": lead.get("Link") or "",
                    "description": lead.get("Descricao (Bio/Web)") or "",
                    "has_phone": lead.get("Tem Telefone?") == "Sim",
                    "has_email": lead.get("Tem E-mail?") == "Sim",
                    "score": 7,
                    "reason": "Lead extraído do motor de busca",
                    "tags": ["Extraído"],
                    "decision_maker": "Proprietario",
                    "whatsapp_ready": True
                }
                if req.min_score <= 7:
                    db.insert_lead(campaign_id, lead_data)
                    approved += 1
                else:
                    discarded += 1

            # Update stats dynamically as leads get processed
            db.update_campaign_stats(campaign_id, total_found=len(leads), total_approved=approved, total_discarded=discarded, status="running")
                
        db.update_campaign_stats(campaign_id, total_found=len(leads), total_approved=approved, total_discarded=discarded, status="completed")
    except Exception as e:
        print(f"[Backend Error] Scrape task failed: {e}")
        db.update_campaign_stats(campaign_id, status="completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
