import json
import flet as ft
from database import get_all_campaigns as db_get_all, create_campaign as db_create, insert_lead as db_insert

def get_campaigns(page: ft.Page):
    return db_get_all()

def save_campaign(page: ft.Page, campaign_data):
    return db_create(**campaign_data)

def add_lead_to_campaign(page: ft.Page, campaign_id, lead_data):
    return db_insert(campaign_id, lead_data)