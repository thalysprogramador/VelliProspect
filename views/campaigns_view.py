import flet as ft
import pandas as pd
import io
import base64
from datetime import datetime
from persistence import get_campaigns, delete_campaign
from database import get_campaign, get_leads_by_campaign, update_lead_status

BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BG_ELEVATED = "#1A1A1A"
BORDER_SUBTLE = "#1F1F1F"
BORDER_HOVER = "#333333"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#8A8A8A"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
SUCCESS = "#34D399"
WARNING = "#FBBF24"
ERROR = "#F87171"

TAG_COLORS = {
    "Ticket Alto": "#10B981", "Ticket Baixo": "#6366F1", "Sem Site": "#EF4444",
    "Boa Presenca Digital": "#3B82F6", "Baixa Presenca Digital": "#F59E0B",
    "Franquia / Rede": "#8B5CF6", "Novo no Mercado": "#EC4899",
    "Decisor Acessivel": "#14B8A6", "Alta Concorrencia": "#F97316",
    "Oportunidade Urgente": "#EAB308", "E-commerce": "#06B6D4",
    "Servico Local": "#84CC16", "B2B": "#6366F1", "B2C": "#F43F5E",
    "Alto Potencial Digital": "#10B981", "Tem Redes Sociais": "#3B82F6",
}

def _status_label(status):
    m = {"running": "Em Andamento", "completed": "Concluida", "failed": "Falhou"}
    return m.get(status, (status or "").capitalize())

def _status_color(status):
    m = {"running": WARNING, "completed": SUCCESS, "failed": ERROR}
    return m.get(status, TEXT_MUTED)

def _format_date(iso_str):
    if not iso_str: return ""
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(iso_str)[:16]

def _build_tag_chip(tag_text):
    color = TAG_COLORS.get(tag_text, "#888888")
    return ft.Container(
        content=ft.Text(tag_text.upper(), size=9, weight=ft.FontWeight.W_700, color=color, font_family="Inter"),
        bgcolor=f"{color}15",
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border_radius=4,
    )

def build_campaigns_view(page: ft.Page):
    campaigns_list = ft.ListView(expand=True, spacing=12, auto_scroll=False)
    detail_panel = ft.Column(expand=True, visible=False, scroll=ft.ScrollMode.AUTO)
    main_container = ft.Column([campaigns_list], expand=True)

    empty_state = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.FOLDER_OPEN, size=56, color=BORDER_HOVER),
            ft.Text("Nenhuma campanha encontrada", size=18, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY, font_family="Inter"),
            ft.Text("Suas buscas concluidas aparecerao aqui.", size=14, color=TEXT_MUTED, font_family="Inter"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=12),
        expand=True,
        alignment=ft.Alignment.CENTER,
        visible=False,
    )

    def load_campaigns():
        campaigns_list.controls.clear()
        detail_panel.visible = False
        main_container.controls = [campaigns_list, empty_state]
        campaigns = get_campaigns(page)

        if not campaigns:
            campaigns_list.visible = False
            empty_state.visible = True
            page.update()
            return

        campaigns_list.visible = True
        empty_state.visible = False

        for c in campaigns:
            c_id = c.get("id")
            total_app = c.get("total_approved") or 0
            status = c.get("status", "")
            s_color = _status_color(status)

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(c.get("name", "Campanha"), size=16, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter", expand=True),
                        ft.Container(
                            content=ft.Text(_status_label(status), size=10, weight=ft.FontWeight.W_800, color=s_color, font_family="Inter"),
                            bgcolor=f"{s_color}15",
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4,
                        ),
                    ]),
                    ft.Text(f"{c.get('niche', '')} em {c.get('region', '')} ({c.get('source', '')})", size=12, color=TEXT_SECONDARY, font_family="Inter"),
                    ft.Divider(color=BORDER_SUBTLE, height=1),
                    ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=TEXT_MUTED),
                            ft.Text(_format_date(c.get("created_at")), size=12, color=TEXT_MUTED, font_family="Inter"),
                        ], spacing=4),
                        ft.Container(expand=True),
                        ft.Row([
                            ft.Icon(ft.Icons.PEOPLE, size=14, color=SUCCESS),
                            ft.Text(f"{total_app} Leads", size=12, weight=ft.FontWeight.W_600, color=SUCCESS, font_family="Inter"),
                        ], spacing=4),
                    ]),
                ], spacing=8),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=12,
                padding=20,
                on_click=lambda e, cid=c_id: show_detail(cid),
                on_hover=lambda e: (setattr(e.control, "border", ft.Border.all(1, ACCENT if e.data == "true" else BORDER_SUBTLE)), e.control.update()),
            )
            campaigns_list.controls.append(card)

        page.update()

    def show_detail(c_id):
        c = get_campaign(c_id)
        if not c: return

        leads = get_leads_by_campaign(c_id)
        detail_panel.controls.clear()

        def on_back(e):
            detail_panel.visible = False
            main_container.controls = [campaigns_list, empty_state]
            page.update()

        def on_delete(e):
            delete_campaign(c_id)
            detail_panel.visible = False
            load_campaigns()

        def on_export(e):
            if not leads: return
            try:
                df = pd.DataFrame(leads)
                cols_drop = ["campaign_id", "id", "created_at"]
                for col in cols_drop:
                    if col in df.columns:
                        df = df.drop(columns=[col])
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                buffer.seek(0)
                b64 = base64.b64encode(buffer.read()).decode()
                page.launch_url(f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}")
            except Exception as ex:
                print(f"[Export Error] {ex}")

        def on_status_change(e, lead_id):
            update_lead_status(lead_id, e.control.value)

        leads_ui = []
        for l in leads:
            score = l.get("score", 0)
            score_color = SUCCESS if score >= 8 else (WARNING if score >= 5 else ERROR)
            tags_ui = [_build_tag_chip(t) for t in l.get("tags", [])]
            lid = l.get("id")

            status_dd = ft.Dropdown(
                options=[
                    ft.dropdown.Option("approved", "Aprovado"),
                    ft.dropdown.Option("contacted", "Contatado"),
                    ft.dropdown.Option("responded", "Respondeu"),
                    ft.dropdown.Option("converted", "Convertido"),
                    ft.dropdown.Option("lost", "Perdido"),
                ],
                value=l.get("status", "approved"),
                width=130,
                height=36,
                text_size=11,
                on_change=lambda e, lid=lid: on_status_change(e, lid),
                bgcolor=BG_PRIMARY,
                border_color=BORDER_SUBTLE,
            )

            leads_ui.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(str(score), size=14, weight=ft.FontWeight.W_800, color=BG_PRIMARY, font_family="Inter"),
                                bgcolor=score_color,
                                width=32, height=32, border_radius=16, alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column([
                                ft.Text(l.get("name", "N/A"), size=15, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                                ft.Text(l.get("link", ""), size=11, color=TEXT_MUTED, font_family="Inter", selectable=True),
                            ], spacing=2, expand=True),
                            status_dd,
                        ]),
                        ft.Row(tags_ui, wrap=True, spacing=4),
                        ft.Text(l.get("reason", ""), size=13, color=TEXT_SECONDARY, font_family="Inter", italic=True),
                    ], spacing=10),
                    bgcolor=BG_PRIMARY,
                    border=ft.Border.all(1, BORDER_SUBTLE),
                    border_radius=8,
                    padding=16,
                )
            )

        detail_panel.controls = [
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, icon_color=TEXT_SECONDARY, on_click=on_back),
                ft.Text(c.get("name"), size=22, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter", expand=True),
                ft.IconButton(ft.Icons.DOWNLOAD, icon_color=TEXT_SECONDARY, on_click=on_export, tooltip="Exportar Excel"),
                ft.IconButton(ft.Icons.DELETE, icon_color=ERROR, on_click=on_delete, tooltip="Apagar Campanha"),
            ]),
            ft.Text(f"Total Aprovados: {len(leads)}", size=14, color=SUCCESS, font_family="Inter"),
            ft.Divider(color=BORDER_SUBTLE),
            ft.Column(leads_ui, spacing=12),
        ]
        detail_panel.visible = True
        main_container.controls = [detail_panel]
        page.update()

    load_campaigns()

    return ft.Container(
        content=ft.Stack([main_container]),
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        expand=True,
    )
