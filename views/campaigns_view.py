"""
Velli Prospect V3 — Campaigns View (Revisado)
Visualizacao de historico de campanhas e exportacao.
"""
import flet as ft
import pandas as pd
import json
import base64
import io
from database import delete_campaign
from persistence import get_campaigns


# Design System
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

def _format_date(iso_str):
    """Formata data ISO para BR."""
    if not iso_str: return "Desconhecido"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return iso_str

def _status_color(status):
    if status == 'completed': return SUCCESS
    if status == 'running': return WARNING
    if status == 'error': return ERROR
    return TEXT_SECONDARY

def _status_label(status):
    if status == 'completed': return "Concluida"
    if status == 'running': return "Rodando"
    if status == 'error': return "Erro"
    return status

def _build_tag_chip(tag_text):
    """Cria um chip de tag minimalista e consistente."""
    from views.prospect_view import TAG_COLORS
    color = TAG_COLORS.get(tag_text, "#6B7280")
    return ft.Container(
        content=ft.Text(tag_text, size=10, color=color, weight=ft.FontWeight.W_600,
                        font_family="Inter"),
        bgcolor=f"{color}15",
        border=ft.Border.all(1, f"{color}40"),
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )


def build_campaigns_view(page: ft.Page):
    """Constroi a view de campanhas."""

    campaigns_list = ft.ListView(spacing=10, expand=True, auto_scroll=False)
    detail_panel = ft.Column(visible=False, expand=True, scroll=ft.ScrollMode.AUTO, spacing=12)

    empty_state = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=TEXT_MUTED),
                ft.Text("Nenhuma campanha salva", size=16, weight=ft.FontWeight.W_600,
                       color=TEXT_SECONDARY, font_family="Inter"),
                ft.Text("Execute uma prospeccao para ver o historico aqui.",
                       size=13, color=TEXT_MUTED, font_family="Inter"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
        visible=False,
    )

    def go_back(e):
        detail_panel.visible = False
        back_button.visible = False
        campaigns_list.visible = True
        empty_state.visible = len(campaigns_list.controls) == 0
        page.update()

    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        icon_color=TEXT_PRIMARY,
        tooltip="Voltar",
        on_click=go_back,
        visible=False,
    )

    def show_detail(campaign_id):
        """Carrega e mostra os leads de uma campanha especifica."""
        from database import get_campaign, get_leads_by_campaign
        campaign = get_campaign(campaign_id)
        leads = get_leads_by_campaign(campaign_id)

        if not campaign: return

        total_approved = campaign.get('total_approved') or 0

        detail_header = ft.Column(
            controls=[
                ft.Text(campaign["name"], size=20, weight=ft.FontWeight.W_700,
                       color=TEXT_PRIMARY, font_family="Inter"),
                ft.Row(
                    controls=[
                        ft.Text(f"{campaign['niche']} em {campaign['region']}",
                               size=13, color=TEXT_SECONDARY, font_family="Inter"),
                        ft.Text("•", size=13, color=TEXT_MUTED),
                        ft.Text(f"{total_approved} aprovados",
                               size=13, weight=ft.FontWeight.W_600, color=SUCCESS, font_family="Inter"),
                    ],
                    spacing=8,
                ),
            ],
            spacing=2,
        )

        export_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, color=BG_PRIMARY, size=16),
                ft.Text("EXPORTAR CSV", size=12, weight=ft.FontWeight.W_600,
                        color=BG_PRIMARY, font_family="Inter"),
            ], spacing=6),
            bgcolor=ACCENT,
            color=BG_PRIMARY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=lambda e: export_to_excel(campaign, leads)
        )

        lead_items = []
        for i, lead in enumerate(leads):
            score = lead.get("score", 0)
            tags = lead.get("tags", [])
            if isinstance(tags, str):
                try: tags = json.loads(tags)
                except: tags = []

            score_color = SUCCESS if score >= 8 else (WARNING if score >= 5 else ERROR)

            tag_row = ft.Row([_build_tag_chip(t) for t in tags[:4]], spacing=6, wrap=True)

            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text(str(i+1), size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
                                            bgcolor="#1F1F1F", border_radius=6, padding=ft.Padding.symmetric(horizontal=8, vertical=4)
                                        ),
                                        ft.Text(lead.get("name", "Desconhecido")[:40], size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ],
                                    spacing=10
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.STAR, size=14, color=score_color),
                                        ft.Text(f"{score}/10", size=14, weight=ft.FontWeight.W_700, color=score_color),
                                    ],
                                    spacing=4
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(lead.get("reason", lead.get("description", ""))[:120], size=12, color=TEXT_SECONDARY, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        tag_row,
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.PERSON_OUTLINE, size=14, color=TEXT_MUTED),
                                        ft.Text(lead.get("decision_maker", "Desconhecido"), size=11, color=TEXT_MUTED),
                                    ],
                                    spacing=4
                                ),
                                ft.Row(
                                    controls=[
                                        ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, icon_size=16, icon_color=TEXT_SECONDARY, tooltip="Link", url=lead.get("link", "")),
                                    ],
                                    spacing=4
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    ],
                    spacing=10
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=12,
                padding=16,
            )
            lead_items.append(card)

        detail_panel.controls = [
            ft.Row([detail_header, export_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10)
        ] + lead_items
        detail_panel.visible = True
        back_button.visible = True
        campaigns_list.visible = False
        empty_state.visible = False
        page.update()

    def export_to_excel(campaign, leads):
        """Gera um arquivo Excel e dispara o download."""
        if not leads: return

        df_data = []
        for lead in leads:
            tags = lead.get("tags", [])
            if isinstance(tags, str):
                try: tags = json.loads(tags)
                except: tags = []

            df_data.append({
                "Nome": lead.get("name", ""),
                "Link/Site": lead.get("link", ""),
                "Score": lead.get("score", 0),
                "Motivo": lead.get("reason", ""),
                "Tags": ", ".join(tags) if isinstance(tags, list) else "",
                "Decisor": lead.get("decision_maker", "Desconhecido"),
                "Descricao": lead.get("description", "")
            })

        df = pd.DataFrame(df_data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads Aprovados')

        excel_data = output.getvalue()
        filename = f"Velli_Leads_{campaign['niche'].replace(' ', '_')}.xlsx"

        # Compatibilidade ASGI/Render e Desktop
        is_web = getattr(page, 'web', True)

        if is_web:
            b64 = base64.b64encode(excel_data).decode()
            page.launch_url(f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}")
        else:
            import os
            path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            try:
                with open(path, "wb") as f:
                    f.write(excel_data)
                page.snack_bar = ft.SnackBar(ft.Text(f"Salvo em: {path}"))
                page.snack_bar.open = True
            except Exception as e:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar: {e}"))
                page.snack_bar.open = True
            page.update()


    def delete_and_refresh(campaign_id):
        delete_campaign(campaign_id)
        load_campaigns()

    def load_campaigns():
        campaigns = get_campaigns(page)
        campaigns_list.controls.clear()
        campaigns_list.visible = True

        if not campaigns:
            empty_state.visible = True
            page.update()
            return

        empty_state.visible = False

        for c in campaigns:
            status_color = _status_color(c["status"])
            total_app = c.get('total_approved') or 0

            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(c["name"], size=14, weight=ft.FontWeight.W_600,
                                       color=TEXT_PRIMARY, font_family="Inter",
                                       max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text(_status_label(c["status"]),
                                                          size=9, color=status_color,
                                                          weight=ft.FontWeight.W_600, font_family="Inter"),
                                            bgcolor=f"{status_color}15",
                                            border_radius=16,
                                            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                        ),
                                        ft.Text(f"{total_app} leads", size=11,
                                               color=TEXT_SECONDARY, font_family="Inter"),
                                        ft.Text(f"• {_format_date(c['created_at'])}",
                                               size=11, color=TEXT_MUTED, font_family="Inter"),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.VISIBILITY,
                                    icon_size=18,
                                    icon_color=TEXT_SECONDARY,
                                    tooltip="Ver detalhes",
                                    on_click=lambda e, cid=c["id"]: show_detail(cid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_size=18,
                                    icon_color=ERROR,
                                    tooltip="Excluir",
                                    on_click=lambda e, cid=c["id"]: delete_and_refresh(cid),
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=12,
                padding=ft.Padding.symmetric(vertical=12, horizontal=16),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                on_hover=lambda e: _on_card_hover(e),
            )
            campaigns_list.controls.append(card)

        page.update()

    def _on_card_hover(e):
        e.control.bgcolor = "#1C1C1C" if e.data == "true" else BG_CARD
        e.control.update()

    load_campaigns()

    view_col = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    back_button,
                    ft.Column(
                        controls=[
                            ft.Text("Campanhas", size=24, weight=ft.FontWeight.W_700,
                                   color=TEXT_PRIMARY, font_family="Inter"),
                            ft.Text("Historico completo de prospeccoes salvas",
                                   size=13, color=TEXT_SECONDARY, font_family="Inter"),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color=TEXT_SECONDARY,
                        icon_size=20,
                        tooltip="Atualizar",
                        on_click=lambda e: load_campaigns(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=8),
            campaigns_list,
            empty_state,
            detail_panel,
        ],
        expand=True,
        spacing=0,
    )

    view = ft.Container(
        content=view_col,
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        expand=True,
    )

    view.on_active = lambda: load_campaigns()

    return view