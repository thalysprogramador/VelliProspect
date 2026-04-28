"""
Velli Prospect V3 — Database Layer (Supabase PostgreSQL)
Gerencia campanhas e leads persistidos na nuvem de forma gratuita.
"""
import os
import json
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = "https://emsejcohbjtymxtahnyb.supabase.co"
SUPABASE_KEY = "sb_publishable_r4Q2eU0K5gL6u6YoeuXCEw_fbJZfFnz"

# Inicialização lenta para evitar erros na importação caso falte env var
_supabase: Client = None

def get_connection():
    """Retorna a instância do Supabase Client."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


# ─── Campaign CRUD ───────────────────────────────────────────

def create_campaign(name, niche, region, source, criteria="", min_score=7, max_results=100):
    """Cria uma nova campanha e retorna o ID."""
    supabase = get_connection()
    data = {
        "name": name,
        "niche": niche,
        "region": region,
        "source": source,
        "criteria": criteria,
        "min_score": min_score,
        "max_results": max_results,
        "status": 'running',
        "created_at": datetime.now().isoformat()
    }
    response = supabase.table("campaigns").insert(data).execute()
    return response.data[0]["id"]


def update_campaign_stats(campaign_id, total_found, total_approved, total_discarded, status="completed"):
    """Atualiza as estatísticas de uma campanha finalizada."""
    supabase = get_connection()
    data = {
        "total_found": total_found,
        "total_approved": total_approved,
        "total_discarded": total_discarded,
        "status": status,
        "finished_at": datetime.now().isoformat()
    }
    supabase.table("campaigns").update(data).eq("id", campaign_id).execute()


def get_all_campaigns():
    """Retorna todas as campanhas ordenadas pela mais recente."""
    supabase = get_connection()
    response = supabase.table("campaigns").select("*").order("created_at", desc=True).execute()
    return response.data


def get_campaign(campaign_id):
    """Retorna uma campanha pelo ID."""
    supabase = get_connection()
    response = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
    return response.data[0] if response.data else None


def delete_campaign(campaign_id):
    """Exclui uma campanha (e seus leads graças ao CASCADE no banco)."""
    supabase = get_connection()
    supabase.table("campaigns").delete().eq("id", campaign_id).execute()


# ─── Lead CRUD ───────────────────────────────────────────────

def insert_lead(campaign_id, lead_data):
    """Insere um lead aprovado no banco."""
    supabase = get_connection()
    
    tags = lead_data.get("tags", [])
    
    data = {
        "campaign_id": campaign_id,
        "name": lead_data.get("name", "Perfil Encontrado"),
        "link": lead_data.get("link", ""),
        "description": lead_data.get("description", ""),
        "has_phone": bool(lead_data.get("has_phone")),
        "has_email": bool(lead_data.get("has_email")),
        "score": int(lead_data.get("score", 0)),
        "reason": str(lead_data.get("reason", "")),
        "tags": tags, # Supabase aceita array diretamente em JSONB
        "decision_maker": str(lead_data.get("decision_maker", "")),
        "whatsapp_ready": bool(lead_data.get("whatsapp_ready")),
        "status": 'approved',
        "created_at": datetime.now().isoformat()
    }
    supabase.table("leads").insert(data).execute()


def get_leads_by_campaign(campaign_id):
    """Retorna todos os leads de uma campanha."""
    supabase = get_connection()
    response = supabase.table("leads").select("*").eq("campaign_id", campaign_id).order("score", desc=True).execute()
    return response.data


def get_all_leads():
    """Retorna todos os leads do banco."""
    supabase = get_connection()
    response = supabase.table("leads").select("*").order("score", desc=True).execute()
    return response.data


# ─── Settings ────────────────────────────────────────────────

def get_setting(key, default=""):
    """Retorna o valor de uma configuração."""
    supabase = get_connection()
    response = supabase.table("settings").select("value").eq("key", key).execute()
    return response.data[0]["value"] if response.data else default


def set_setting(key, value):
    """Salva ou atualiza uma configuração."""
    supabase = get_connection()
    # Supabase UPSERT require table PKs and data
    data = {"key": key, "value": value}
    supabase.table("settings").upsert(data).execute()
