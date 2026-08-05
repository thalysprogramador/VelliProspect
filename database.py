"""
Velli Prospect V3 — Database Layer (Supabase PostgreSQL)
Gerencia campanhas e leads persistidos na nuvem.
"""
import os
import json
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = "https://emsejcohbjtymxtahnyb.supabase.co"
SUPABASE_KEY = "sb_publishable_r4Q2eU0K5gL6u6YoeuXCEw_fbJZfFnz"

_supabase = None

def get_connection():
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

def _safe_execute(func, default_return=None):
    try:
        return func()
    except Exception as e:
        print(f"[DB Error] Falha de conexao com Supabase: {e}")
        return default_return

def create_campaign(name, niche, region, source, criteria="", min_score=7, max_results=100):
    supabase = get_connection()
    data = {
        "name": name,
        "niche": niche,
        "region": region,
        "source": source,
        "criteria": criteria,
        "min_score": min_score,
        "max_results": max_results,
        "status": "running",
        "created_at": datetime.now().isoformat()
    }
    response = _safe_execute(lambda: supabase.table("campaigns").insert(data).execute())
    return response.data[0]["id"] if response and response.data else "temp_" + str(int(datetime.now().timestamp()))

def update_campaign_stats(campaign_id, total_found, total_approved, total_discarded, status="completed"):
    if str(campaign_id).startswith("temp_"): return
    supabase = get_connection()
    data = {
        "total_found": total_found,
        "total_approved": total_approved,
        "total_discarded": total_discarded,
        "status": status,
        "finished_at": datetime.now().isoformat()
    }
    _safe_execute(lambda: supabase.table("campaigns").update(data).eq("id", campaign_id).execute())

def get_all_campaigns():
    supabase = get_connection()
    response = _safe_execute(lambda: supabase.table("campaigns").select("*").order("created_at", desc=True).execute())
    return response.data if response and response.data else []

def get_campaign(campaign_id):
    supabase = get_connection()
    response = _safe_execute(lambda: supabase.table("campaigns").select("*").eq("id", campaign_id).execute())
    return response.data[0] if response and response.data else None

def delete_campaign(campaign_id):
    supabase = get_connection()
    _safe_execute(lambda: supabase.table("campaigns").delete().eq("id", campaign_id).execute())

def insert_lead(campaign_id, lead_data):
    if str(campaign_id).startswith("temp_"): return
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
        "tags": tags,
        "decision_maker": str(lead_data.get("decision_maker", "")),
        "whatsapp_ready": bool(lead_data.get("whatsapp_ready")),
        "status": "approved",
        "created_at": datetime.now().isoformat()
    }
    _safe_execute(lambda: supabase.table("leads").insert(data).execute())

def update_lead_status(lead_id, status):
    supabase = get_connection()
    data = {"status": status}
    _safe_execute(lambda: supabase.table("leads").update(data).eq("id", lead_id).execute())

def get_leads_by_campaign(campaign_id):
    supabase = get_connection()
    response = _safe_execute(lambda: supabase.table("leads").select("*").eq("campaign_id", campaign_id).order("score", desc=True).execute())
    return response.data if response and response.data else []

def get_leads_by_status(status):
    supabase = get_connection()
    response = _safe_execute(lambda: supabase.table("leads").select("*").eq("status", status).order("score", desc=True).execute())
    return response.data if response and response.data else []

def get_all_leads():
    supabase = get_connection()
    response = _safe_execute(lambda: supabase.table("leads").select("*").order("score", desc=True).execute())
    return response.data if response and response.data else []

def get_setting(key, default=""):
    supabase = get_connection()
    response = _safe_execute(lambda: supabase.table("settings").select("value").eq("key", key).execute())
    return response.data[0]["value"] if response and response.data else default

def set_setting(key, value):
    supabase = get_connection()
    data = {"key": key, "value": value}
    _safe_execute(lambda: supabase.table("settings").upsert(data).execute())