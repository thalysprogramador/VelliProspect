
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union, List
import database as db
import scraper
import ai_evaluator
import math

active_campaigns = {}

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
    source: Union[List[str], str]
    criteria: str = ""
    min_score: int = 7
    max_results: int = 50
    block_large_portals: bool = True

class SettingsRequest(BaseModel):
    key: str
    value: str

class CopilotRequest(BaseModel):
    message: str
    history: list = []  # opcional, historico anterior do chat

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
    active_campaigns[campaign_id] = False
    db.delete_campaign(campaign_id)
    return {"status": "deleted"}

@app.post("/api/campaigns/{campaign_id}/cancel")
def cancel_campaign(campaign_id: str):
    active_campaigns[campaign_id] = False
    db.update_campaign_stats(campaign_id, status="completed")
    return {"status": "cancelled"}

@app.get("/api/settings/{key}")
def get_setting(key: str):
    val = db.get_setting(key)
    return {"key": key, "value": val}

@app.post("/api/settings")
def set_setting(req: SettingsRequest):
    db.set_setting(req.key, req.value)
    return {"status": "success"}

@app.post("/api/copilot/chat")
def copilot_chat_endpoint(req: CopilotRequest):
    api_key = db.get_setting("gemini_api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Configure a API Key na aba Configuracoes primeiro.")
    
    # We fetch leads to give context to Gemini
    leads = db.get_all_leads()
    
    # Include history in the message if it exists so Gemini has context
    full_message = req.message
    if req.history:
        history_text = "\n".join([f"{msg['role'].upper()}: {msg['text']}" for msg in req.history[-5:]]) # ultimas 5 mensagens
        full_message = f"HISTORICO DA CONVERSA:\n{history_text}\n\nNOVA MENSAGEM DO USUARIO:\n{req.message}"
        
    try:
        reply = ai_evaluator.copilot_chat(full_message, leads, api_key)
        return {"reply": reply}
    except Exception as e:
        print(f"[Copilot Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns")
def create_campaign(req: ScrapeRequest, background_tasks: BackgroundTasks):
    camp_name = f"{req.niche} em {req.region}"
    cid = db.create_campaign(camp_name, req.niche, req.region, req.source, req.criteria, req.min_score, req.max_results)
    if not cid:
        raise HTTPException(status_code=500, detail="Error creating campaign")
    
    background_tasks.add_task(run_scrape_task, cid, req)
    return {"status": "started", "campaign": {"id": cid}}

def run_scrape_task(campaign_id: str, req: ScrapeRequest):
    active_campaigns[campaign_id] = True
    try:
        leads = scraper.scrape_leads(
            req.niche, req.region, req.source, 
            req.max_results, req.block_large_portals
        )
        if not leads:
            db.delete_campaign(campaign_id)
            return
            
        db.update_campaign_stats(campaign_id, total_found=len(leads))
        
        api_key = db.get_setting("gemini_api_key", "")
        approved = 0
        discarded = 0
        
        batch_size = 10
        for i in range(0, len(leads), batch_size):
            if not active_campaigns.get(campaign_id, True):
                print(f"[Backend] Campaign {campaign_id} cancelled.")
                break
                
            if approved >= req.max_results:
                break # We hit the exact target!
                
            batch = leads[i:i + batch_size]
            try:
                evaluated_batch = ai_evaluator.evaluate_leads_batch(batch, api_key, req.criteria)
                
                for idx, lead in enumerate(batch):
                    if approved >= req.max_results:
                        break # Stop evaluating if we hit target inside the batch
                        
                    evaluated = evaluated_batch[idx] if idx < len(evaluated_batch) else {}
                    score = evaluated.get("score", 5)
                    
                    if score >= req.min_score:
                        lead_data = {
                            "name": lead.get("Nome") or lead.get("name") or "Lead Encontrado",
                            "link": lead.get("Link") or lead.get("link") or "",
                            "description": lead.get("Descricao (Bio/Web)") or lead.get("description") or "",
                            "has_phone": lead.get("Tem Telefone?") == "Sim" or bool(lead.get("has_phone")),
                            "has_email": lead.get("Tem E-mail?") == "Sim" or bool(lead.get("has_email")),
                            "score": score,
                            "reason": evaluated.get("reason", "Lead avaliado"),
                            "tags": evaluated.get("tags", []),
                            "decision_maker": evaluated.get("decision_maker", "Proprietario"),
                            "whatsapp_ready": evaluated.get("whatsapp_ready", True),
                            "source": lead.get("_source", "") # Tag with source
                        }
                        db.insert_lead(campaign_id, lead_data)
                        approved += 1
                    else:
                        discarded += 1
            except Exception as e:
                print(f"[Backend Error] Batch evaluation failed: {e}")
                # Fallback para o lote
                for lead in batch:
                    if approved >= req.max_results:
                        break
                        
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
                        "whatsapp_ready": True,
                        "source": lead.get("_source", "")
                    }
                    if req.min_score <= 7:
                        db.insert_lead(campaign_id, lead_data)
                        approved += 1
                    else:
                        discarded += 1

            # Update stats dynamically after each batch
            db.update_campaign_stats(campaign_id, total_found=len(leads), total_approved=approved, total_discarded=discarded, status="running")
                
        # End of loop
        if approved == 0:
            print(f"[Backend] Campaign {campaign_id} deleted because 0 leads were approved.")
            db.delete_campaign(campaign_id)
        else:
            db.update_campaign_stats(campaign_id, total_found=len(leads), total_approved=approved, total_discarded=discarded, status="completed")
    except Exception as e:
        print(f"[Backend Error] Scrape task failed: {e}")
        db.delete_campaign(campaign_id)
    finally:
        active_campaigns.pop(campaign_id, None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
