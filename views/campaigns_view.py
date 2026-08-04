import flet as ft
import pandas as pd
import json
import base64
import io
import threading
from database import delete_campaign, get_campaign, get_leads_by_campaign, update_lead_status
from persistence import get_campaigns
from datetime import datetime

BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BORDER_SUBTLE = "#2A2A2A"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
SUCCESS = "#4ADE80"
WARNING = "#FBBF24"
ERROR = "#F87171"

TAG_COLORS = {
    "Ticket Alto": "#10B981", "Ticket Baixo": "#6366F1", "Sem Site": "#EF4444",
    "Boa Presenca Digital": "#3B82F6", "Baixa Presenca Digital": "#F59E0B",
    "Franquia / Rede": "#8B5CF6", "Novo no Mercado": "#EC4899",
    "Decisor Acessivel": "#14B8A6", "Alta Concorrencia": "#F97316",
    "Oportunidade Urgente": "#EAB308", "E-commerce": "#06B6D4",
    "Servico Local": "#84CC16", "B2B": "#6366F1", "B2C": "#F43F5E",
    "Alto Potencial Digital": "#10B981", "Tem Redes Sociais": "#3B82F6"
}

def _format_date(iso_str):
    if not iso_str: return "Desconhecida"
    try:
        dt = datetime.fromisoformat(iso_str.split(".")[0])
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return iso_str

def _status_color(status):
    if status == 'running': return WARNING
    if status == 'completed': return SUCCESS
    return ERROR

def _status_label(status):
    if status == 'running': return "EM ANDAMENTO"
    if status == 'completed': return "CONCLUIDO"
    return "ERRO"

def _build_tag_chip(tag_text):
    color = TAG_COLORS.get(tag_text, "#888888")
    return ft.Container(
        content=ft.Text(tag_text.upper(), size=9, weight=ft.FontWeight.W_700,
                       color=color, font_family="Inter"),
        bgcolor=f"{color}15",
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border_radius=4,
    )

def build_campaigns_view(page: ft.Page):
    campaigns_list = ft.ListView(expand=True, spacing=15, auto_scroll=False)
    detail_panel = ft.Column(expand=True, visible=False, scroll=ft.ScrollMode.AUTO)
    main_container = ft.Row([campaigns_list, detail_panel], expand=True, spacing=20)
    
    empty_state = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=BORDER_SUBTLE),
                ft.Text("Nenhuma campanha encontrada", size=18, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY, font_family="Inter"),
                ft.Text("Suas buscas concluidas aparecerao aqui.", size=14, color=TEXT_MUTED, font_family="Inter"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        alignment=ft.Alignment.CENTER,
        visible=False
    )

    def load_campaigns():
        campaigns_list.controls.clear()
        campaigns = get_campaigns(page)
        
        if not campaigns:
            campaigns_list.visible = False
            empty_state.visible = True
            page.update()
            return
            
        campaigns_list.visible = True
        empty_state.visible = False

        for c in campaigns:
            c_id = c.get('id')
            total_app = c.get('total_approved') or 0
            
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(c.get('name', 'Campanha'), size=16, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter", expand=True),
                        ft.Container(
                            content=ft.Text(_status_label(c.get('status')), size=10, weight=ft.FontWeight.W_800, color=_status_color(c.get('status')), font_family="Inter"),
                            bgcolor=f"{_status_color(c.get('status'))}15",
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4
                        )
                    ]),
                    ft.Text(f"{c.get('niche')} em {c.get('region')} ({c.get('source')})", size=12, color=TEXT_SECONDARY, font_family="Inter"),
                    ft.Divider(color=BORDER_SUBTLE, height=1),
                    ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=TEXT_MUTED),
                        ft.Text(_format_date(c.get('created_at')), size=12, color=TEXT_MUTED, font_family="Inter"),
                        ft.Container(expand=True),
                        ft.Icon(ft.Icons.PEOPLE, size=14, color=SUCCESS),
                        ft.Text(f"{total_app} Leads", size=12, weight=ft.FontWeight.W_600, color=SUCCESS, font_family="Inter"),
                    ])
                ], spacing=8),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=12,
                padding=20,
                on_click=lambda e, cid=c_id: show_detail(cid),
                on_hover=lambda e: (setattr(e.control, 'border', ft.Border.all(1, ACCENT if e.data == "true" else BORDER_SUBTLE)), e.control.update())
            )
            campaigns_list.controls.append(card)
        
        page.update()

    def delete_and_refresh(c_id):
        delete_campaign(c_id)
        detail_panel.visible = False
        load_campaigns()

    def update_lead_status_ui(e, lead_id):
        new_status = e.control.value
        update_lead_status(lead_id, new_status)
        page.snack_bar = ft.SnackBar(ft.Text(f"Status atualizado para: {new_status}"))
        page.snack_bar.open = True
        page.update()

    def show_detail(c_id):
        c = get_campaign(c_id)
        if not c: return
        
        leads = get_leads_by_campaign(c_id)
        
        leads_ui = []
        for l in leads:
            tags_ui = [_build_tag_chip(t) for t in l.get('tags', [])]
            
            status_dropdown = ft.Dropdown(
                options=[
                    ft.dropdown.Option("approved", "Aprovado"),
                    ft.dropdown.Option("contacted", "Contatado"),
                    ft.dropdown.Option("responded", "Respondeu"),
                    ft.dropdown.Option("converted", "Convertido"),
                    ft.dropdown.Option("lost", "Perdido"),
                ],
                value=l.get('status', 'approved'),
                width=120,
                height=35,
                text_size=12,
                on_change=lambda e, lid=l['id']: update_lead_status_ui(e, lid),
                bgcolor=BG_PRIMARY,
                border_color=BORDER_SUBTLE
            )
            
            leads_ui.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(str(l.get('score', 0)), size=16, weight=ft.FontWeight.W_800, color=BG_PRIMARY, font_family="Inter"),
                                bgcolor=SUCCESS if l.get('score',0) >= 8 else WARNING if l.get('score',0) >= 5 else ERROR,
                                width=32, height=32, border_radius=16, alignment=ft.Alignment.CENTER
                            ),
                            ft.Column([
                                ft.Text(l.get('name', 'N/A'), size=16, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                                ft.Text(l.get('link', ''), size=12, color=TEXT_SECONDARY, font_family="Inter", selectable=True)
                            ], spacing=2, expand=True),
                            status_dropdown
                        ]),
                        ft.Row(tags_ui, wrap=True, spacing=4),
                        ft.Text(l.get('reason', ''), size=13, color=TEXT_SECONDARY, font_family="Inter", italic=True),
                    ], spacing=10),
                    bgcolor=BG_PRIMARY,
                    border=ft.Border.all(1, BORDER_SUBTLE),
                    border_radius=8,
                    padding=15
                )
            )

        def export_to_excel(e):
            if not leads: return
            df = pd.DataFrame(leads)
            
            # Limpeza
            cols_to_drop = ['campaign_id', 'id', 'created_at']
            for col in cols_to_drop:
                if col in df.columns:
                    df = df.drop(columns=[col])
                    
            if getattr(page, 'web', True):
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                buffer.seek(0)
                b64 = base64.b64encode(buffer.read()).decode()
                page.launch_url(f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}")
            else:
                pass # Web first

        detail_panel.controls = [
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: (setattr(detail_panel, 'visible', False), page.update())),
                ft.Text(c.get('name'), size=20, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter", expand=True),
                ft.IconButton(ft.Icons.DOWNLOAD, on_click=export_to_excel, tooltip="Exportar Excel"),
                ft.IconButton(ft.Icons.DELETE, icon_color=ERROR, on_click=lambda e: delete_and_refresh(c_id), tooltip="Apagar Campanha")
            ]),
            ft.Text(f"Total Aprovados: {len(leads)}", size=14, color=SUCCESS, font_family="Inter"),
            ft.Divider(color=BORDER_SUBTLE),
            ft.Column(leads_ui, spacing=15)
        ]
        detail_panel.visible = True
        page.update()

    load_campaigns()
    
    return ft.Container(
        content=ft.Stack([main_container, empty_state]),
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        expand=True,
    )