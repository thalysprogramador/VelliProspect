import json
import flet as ft
from database import get_all_campaigns as db_get_all, create_campaign as db_create, insert_lead as db_insert

def get_campaigns(page: ft.Page):
    """Retorna campanhas usando o Supabase."""
    return db_get_all()

def save_campaign(page: ft.Page, campaign_data):
    """Salva uma nova campanha."""
    return db_create(**campaign_data)

def add_lead_to_campaign(page: ft.Page, campaign_id, lead_data):
    """Adiciona um lead a uma campanha específica."""
    return db_insert(campaign_id, lead_data)
