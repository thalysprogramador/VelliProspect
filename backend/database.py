"""
Velli Prospect V3 - Database Layer
Supabase com fallback local via JSON.
"""
import os
import json
from datetime import datetime

# === Supabase Config ===
SUPABASE_URL = "https://emsejcohbjtymxtahnyb.supabase.co"
SUPABASE_KEY = "sb_publishable_r4Q2eU0K5gL6u6YoeuXCEw_fbJZfFnz"

# === Fallback Local ===
LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_data.json")

# Gemini API Key default (pre-salva)
DEFAULT_GEMINI_KEY = "AIzaSyBpoZCXXetdIOzUCSUPN-P1wY9DsbxaJ1I"

_supabase = None
_use_local = False

def _load_local_db():
    if os.path.exists(LOCAL_DB_PATH):
        try:
            with open(LOCAL_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"campaigns": [], "leads": [], "settings": {}}

def _save_local_db(data):
    try:
        with open(LOCAL_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DB] Erro ao salvar local: {e}")

def get_connection():
    global _supabase, _use_local
    if _supabase is not None:
        return _supabase
    try:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Quick connectivity check
        _supabase.table("settings").select("key").limit(1).execute()
        print("[DB] Supabase conectado com sucesso")
        _use_local = False
        return _supabase
    except Exception as e:
        print(f"[DB] Supabase offline: {e}. Usando armazenamento local.")
        _use_local = True
        return None

def _safe_execute(func, default_return=None):
    global _use_local
    if _use_local:
        return default_return
    try:
        return func()
    except Exception as e:
        err = str(e)
        print(f"[DB Error] {err}")
        if "getaddrinfo" in err or "connect" in err.lower() or "resolve" in err.lower():
            _use_local = True
            print("[DB] Switching to local storage")
        return default_return

# === Campaigns ===
def create_campaign(name="", niche="", region="", source="", criteria="", min_score=7, max_results=100):
    data = {
        "name": name, "niche": niche, "region": region, "source": source,
        "criteria": criteria, "min_score": min_score, "max_results": max_results,
        "status": "running", "created_at": datetime.now().isoformat(),
    }
    supabase = get_connection()
    if not _use_local and supabase:
        response = _safe_execute(lambda: supabase.table("campaigns").insert(data).execute())
        if response and response.data:
            return response.data[0]["id"]

    db = _load_local_db()
    import uuid
    cid = str(uuid.uuid4())
    data["id"] = cid
    data["total_approved"] = 0
    data["total_found"] = 0
    data["total_discarded"] = 0
    db["campaigns"].insert(0, data)
    _save_local_db(db)
    return cid

def update_campaign_stats(campaign_id, total_found=0, total_approved=0, total_discarded=0, status="completed"):
    update_data = {
        "total_found": total_found, "total_approved": total_approved,
        "total_discarded": total_discarded, "status": status,
        "finished_at": datetime.now().isoformat(),
    }
    supabase = get_connection()
    if not _use_local and supabase:
        _safe_execute(lambda: supabase.table("campaigns").update(update_data).eq("id", campaign_id).execute())
        return

    db = _load_local_db()
    for c in db["campaigns"]:
        if c.get("id") == campaign_id:
            c.update(update_data)
            break
    _save_local_db(db)

def get_all_campaigns():
    supabase = get_connection()
    if not _use_local and supabase:
        response = _safe_execute(lambda: supabase.table("campaigns").select("*").order("created_at", desc=True).execute())
        if response and response.data:
            return response.data

    db = _load_local_db()
    return db.get("campaigns", [])

def get_campaign(campaign_id):
    supabase = get_connection()
    if not _use_local and supabase:
        response = _safe_execute(lambda: supabase.table("campaigns").select("*").eq("id", campaign_id).execute())
        if response and response.data:
            return response.data[0]

    db = _load_local_db()
    for c in db.get("campaigns", []):
        if c.get("id") == campaign_id:
            return c
    return None

def delete_campaign(campaign_id):
    supabase = get_connection()
    if not _use_local and supabase:
        _safe_execute(lambda: supabase.table("campaigns").delete().eq("id", campaign_id).execute())
        _safe_execute(lambda: supabase.table("leads").delete().eq("campaign_id", campaign_id).execute())
        return

    db = _load_local_db()
    db["campaigns"] = [c for c in db["campaigns"] if c.get("id") != campaign_id]
    db["leads"] = [l for l in db["leads"] if l.get("campaign_id") != campaign_id]
    _save_local_db(db)

# === Leads ===
def insert_lead(campaign_id, lead_data):
    data = {
        "campaign_id": campaign_id,
        "name": lead_data.get("name", ""),
        "link": lead_data.get("link", ""),
        "description": lead_data.get("description", ""),
        "has_phone": bool(lead_data.get("has_phone")),
        "has_email": bool(lead_data.get("has_email")),
        "score": int(lead_data.get("score", 0)),
        "reason": str(lead_data.get("reason", "")),
        "tags": lead_data.get("tags", []),
        "decision_maker": str(lead_data.get("decision_maker", "")),
        "whatsapp_ready": bool(lead_data.get("whatsapp_ready")),
        "status": "approved",
        "created_at": datetime.now().isoformat(),
    }

    supabase = get_connection()
    if not _use_local and supabase:
        _safe_execute(lambda: supabase.table("leads").insert(data).execute())
        return

    db = _load_local_db()
    import uuid
    data["id"] = str(uuid.uuid4())
    db["leads"].insert(0, data)
    _save_local_db(db)

def update_lead_status(lead_id, status):
    supabase = get_connection()
    if not _use_local and supabase:
        _safe_execute(lambda: supabase.table("leads").update({"status": status}).eq("id", lead_id).execute())
        return

    db = _load_local_db()
    for l in db["leads"]:
        if l.get("id") == lead_id:
            l["status"] = status
            break
    _save_local_db(db)

def get_leads_by_campaign(campaign_id):
    supabase = get_connection()
    if not _use_local and supabase:
        response = _safe_execute(lambda: supabase.table("leads").select("*").eq("campaign_id", campaign_id).order("score", desc=True).execute())
        if response and response.data:
            return response.data

    db = _load_local_db()
    return sorted([l for l in db.get("leads", []) if l.get("campaign_id") == campaign_id], key=lambda x: x.get("score", 0), reverse=True)

def get_all_leads():
    supabase = get_connection()
    if not _use_local and supabase:
        response = _safe_execute(lambda: supabase.table("leads").select("*").order("score", desc=True).execute())
        if response and response.data:
            return response.data

    db = _load_local_db()
    return sorted(db.get("leads", []), key=lambda x: x.get("score", 0), reverse=True)

def get_leads_by_status(status):
    supabase = get_connection()
    if not _use_local and supabase:
        response = _safe_execute(lambda: supabase.table("leads").select("*").eq("status", status).order("score", desc=True).execute())
        if response and response.data:
            return response.data
    db = _load_local_db()
    return [l for l in db.get("leads", []) if l.get("status") == status]

# === Settings ===
def get_setting(key, default=""):
    supabase = get_connection()
    if not _use_local and supabase:
        response = _safe_execute(lambda: supabase.table("settings").select("value").eq("key", key).execute())
        if response and response.data:
            return response.data[0]["value"]

    db = _load_local_db()
    val = db.get("settings", {}).get(key, "")
    if val:
        return val

    if key == "gemini_api_key" and DEFAULT_GEMINI_KEY:
        return DEFAULT_GEMINI_KEY

    return default

def set_setting(key, value):
    supabase = get_connection()
    if not _use_local and supabase:
        _safe_execute(lambda: supabase.table("settings").upsert({"key": key, "value": value}).execute())
        # Also save locally as backup
    db = _load_local_db()
    if "settings" not in db:
        db["settings"] = {}
    db["settings"][key] = value
    _save_local_db(db)
