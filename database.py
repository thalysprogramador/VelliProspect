"""
Velli Prospect V3 — Database Layer (SQLite)
Gerencia campanhas e leads persistidos localmente.
Funciona tanto no PC quanto no celular (Android via Flet).
"""
import sqlite3
import json
import os
from datetime import datetime


def _get_db_path():
    """Retorna o caminho do banco de dados, compatível com desktop e mobile."""
    # No Android, o Flet define um diretório de dados do app através de FLET_APP_STORAGE_DATA.
    # No desktop (PyInstaller), arquivos sofrem flush em Temp, logo forçamos um local estático e seguro.
    data_dir = os.environ.get("FLET_APP_STORAGE_DATA")
    
    if not data_dir:
        home_dir = os.path.expanduser("~")
        data_dir = os.path.join(home_dir, ".velli")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            
    return os.path.join(data_dir, "velli_prospect_v3.db")


def get_connection():
    """Cria e retorna uma conexão com o banco SQLite."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Inicializa as tabelas do banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            niche TEXT NOT NULL,
            region TEXT NOT NULL,
            source TEXT NOT NULL,
            criteria TEXT,
            min_score INTEGER DEFAULT 7,
            max_results INTEGER DEFAULT 100,
            status TEXT DEFAULT 'pending',
            total_found INTEGER DEFAULT 0,
            total_approved INTEGER DEFAULT 0,
            total_discarded INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            finished_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            link TEXT,
            description TEXT,
            has_phone INTEGER DEFAULT 0,
            has_email INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            reason TEXT,
            tags TEXT,
            decision_maker TEXT,
            whatsapp_ready INTEGER DEFAULT 0,
            status TEXT DEFAULT 'approved',
            created_at TEXT NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


# ─── Campaign CRUD ───────────────────────────────────────────

def create_campaign(name, niche, region, source, criteria="", min_score=7, max_results=100):
    """Cria uma nova campanha e retorna o ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaigns (name, niche, region, source, criteria, min_score, max_results, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?)
    """, (name, niche, region, source, criteria, min_score, max_results, datetime.now().isoformat()))
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id


def update_campaign_stats(campaign_id, total_found, total_approved, total_discarded, status="completed"):
    """Atualiza as estatísticas de uma campanha finalizada."""
    conn = get_connection()
    conn.execute("""
        UPDATE campaigns SET total_found=?, total_approved=?, total_discarded=?, status=?, finished_at=?
        WHERE id=?
    """, (total_found, total_approved, total_discarded, status, datetime.now().isoformat(), campaign_id))
    conn.commit()
    conn.close()


def get_all_campaigns():
    """Retorna todas as campanhas ordenadas pela mais recente."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_campaign(campaign_id):
    """Retorna uma campanha pelo ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_campaign(campaign_id):
    """Exclui uma campanha e seus leads."""
    conn = get_connection()
    conn.execute("DELETE FROM leads WHERE campaign_id=?", (campaign_id,))
    conn.execute("DELETE FROM campaigns WHERE id=?", (campaign_id,))
    conn.commit()
    conn.close()


# ─── Lead CRUD ───────────────────────────────────────────────

def insert_lead(campaign_id, lead_data):
    """Insere um lead aprovado no banco."""
    conn = get_connection()
    tags_json = json.dumps(lead_data.get("tags", []), ensure_ascii=False)
    conn.execute("""
        INSERT INTO leads (campaign_id, name, link, description, has_phone, has_email, 
                          score, reason, tags, decision_maker, whatsapp_ready, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?)
    """, (
        campaign_id,
        lead_data.get("name", "Perfil Encontrado"),
        lead_data.get("link", ""),
        lead_data.get("description", ""),
        1 if lead_data.get("has_phone") else 0,
        1 if lead_data.get("has_email") else 0,
        lead_data.get("score", 0),
        lead_data.get("reason", ""),
        tags_json,
        lead_data.get("decision_maker", ""),
        1 if lead_data.get("whatsapp_ready") else 0,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_leads_by_campaign(campaign_id):
    """Retorna todos os leads de uma campanha."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM leads WHERE campaign_id=? ORDER BY score DESC", (campaign_id,)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        try:
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
        except json.JSONDecodeError:
            d["tags"] = []
        results.append(d)
    return results


def get_all_leads():
    """Retorna todos os leads do banco."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM leads ORDER BY score DESC").fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        try:
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
        except json.JSONDecodeError:
            d["tags"] = []
        results.append(d)
    return results


# ─── Settings ────────────────────────────────────────────────

def get_setting(key, default=""):
    """Retorna o valor de uma configuração."""
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    """Salva ou atualiza uma configuração."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


# Inicializar automaticamente ao importar
init_db()
