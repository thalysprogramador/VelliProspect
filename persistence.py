import json
import flet as ft
from database import get_all_campaigns as db_get_all, create_campaign as db_create, insert_lead as db_insert

def get_campaigns(page: ft.Page):
    """Retorna campanhas (do banco se Desktop, do navegador se Web)."""
    if not page.web:
        return db_get_all()
    
    # Lógica Web: Client Storage
    data = page.client_storage.get("velli_campaigns")
    return json.loads(data) if data else []

def save_campaign(page: ft.Page, campaign_data):
    """Salva uma nova campanha."""
    if not page.web:
        # No desktop, o database.py já cuida disso no fluxo normal
        # Mas vamos retornar o ID do banco
        return db_create(**campaign_data)
    
    # Lógica Web: Client Storage
    campaigns = get_campaigns(page)
    new_id = len(campaigns) + 1
    campaign_data["id"] = new_id
    campaign_data["leads"] = []
    campaign_data["status"] = "completed"
    campaigns.insert(0, campaign_data)
    page.client_storage.set("velli_campaigns", json.dumps(campaigns))
    return new_id

def add_lead_to_campaign(page: ft.Page, campaign_id, lead_data):
    """Adiciona um lead a uma campanha específica."""
    if not page.web:
        return db_insert(campaign_id, lead_data)
    
    # Lógica Web: Client Storage
    campaigns = get_campaigns(page)
    for c in campaigns:
        if c["id"] == campaign_id:
            if "leads" not in c: c["leads"] = []
            c["leads"].append(lead_data)
            c["total_approved"] = len(c["leads"])
            break
    page.client_storage.set("velli_campaigns", json.dumps(campaigns))
