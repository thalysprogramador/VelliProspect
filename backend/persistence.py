from database import (
    get_all_campaigns as db_get_all, create_campaign as db_create,
    insert_lead as db_insert, delete_campaign as db_delete,
)

def get_campaigns(page=None):
    return db_get_all()

def save_campaign(page=None, campaign_data=None):
    if campaign_data is None: campaign_data = {}
    return db_create(name=campaign_data.get("name",""), niche=campaign_data.get("niche",""), region=campaign_data.get("region",""), source=campaign_data.get("source",""), criteria=campaign_data.get("criteria",""), min_score=campaign_data.get("min_score",7), max_results=campaign_data.get("max_results",100))

def add_lead_to_campaign(page=None, campaign_id=None, lead_data=None):
    if lead_data is None: lead_data = {}
    return db_insert(campaign_id, lead_data)

def delete_campaign(campaign_id):
    return db_delete(campaign_id)