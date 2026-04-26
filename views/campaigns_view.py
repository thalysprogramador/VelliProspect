"""
Velli Prospect V3 — Campaigns View
Tela de histórico de campanhas salvas com detalhamento de leads.
"""
import flet as ft
from database import get_all_campaigns, get_leads_by_campaign, delete_campaign
from persistence import get_campaigns, add_lead_to_campaign
import pandas as pd
import io
import base64

# ─── Design System ───────────────────────────────────────────
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
    "Ticket Alto": "#22C55E",
    "Ticket Baixo": "#F97316",
    "Sem Site": "#EF4444",
    "Boa Presença Digital": "#3B82F6",
    "Baixa Presença Digital": "#F59E0B",
    "Franquia / Rede": "#8B5CF6",
    "Novo no Mercado": "#06B6D4",
    "Decisor Acessível": "#10B981",
    "Alta Concorrência": "#F43F5E",
    "Oportunidade Urgente": "#E11D48",
    "Erro": "#6B7280",
}


def _format_date(iso_str):
    """Formata data ISO para exibição amigável."""
    if not iso_str:
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return iso_str[:16]


def _status_color(status):
    """Retorna a cor baseada no status da campanha."""
    return {
        "completed": SUCCESS,
        "running": WARNING,
        "pending": TEXT_MUTED,
        "empty": ERROR,
    }.get(status, TEXT_MUTED)


def _status_label(status):
    """Retorna o label do status em PT-BR."""
    return {
        "completed": "Concluída",
        "running": "Em Andamento",
        "pending": "Pendente",
        "empty": "Sem Resultados",
    }.get(status, status)


def build_campaigns_view(page: ft.Page):
    """Constrói a view de campanhas salvas."""

    campaigns_list = ft.ListView(
        spacing=12,
        padding=ft.Padding.only(top=10),
        expand=True,
    )

    detail_panel = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        visible=False,
    )

    empty_state = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=TEXT_MUTED),
                ft.Text("Nenhuma campanha ainda", size=16, color=TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500, font_family="Inter"),
                ft.Text("Execute sua primeira prospecção na aba ao lado.",
                        size=12, color=TEXT_MUTED, font_family="Inter"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
        padding=40,
    )

    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        icon_color=TEXT_SECONDARY,
        icon_size=20,
        tooltip="Voltar para lista",
        visible=False,
        on_click=lambda e: show_list(),
    )

    def show_list():
        """Mostra a lista de campanhas."""
        detail_panel.visible = False
        detail_panel.controls.clear()
        back_button.visible = False
        load_campaigns()

    def show_detail(campaign_id):
        """Mostra os detalhes de uma campanha."""
        campaign = None
        for c in get_all_campaigns():
            if c["id"] == campaign_id:
                campaign = c
                break

        if not campaign:
            return

        leads = get_leads_by_campaign(campaign_id)

        # Header da campanha
        detail_header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(campaign["name"], size=18, weight=ft.FontWeight.W_700,
                           color=TEXT_PRIMARY, font_family="Inter"),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(_status_label(campaign["status"]),
                                              size=10, color=_status_color(campaign["status"]),
                                              weight=ft.FontWeight.W_600, font_family="Inter"),
                                bgcolor=f"{_status_color(campaign['status'])}15",
                                border_radius=20,
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            ),
                            ft.Text(f"📅 {_format_date(campaign['created_at'])}",
                                   size=11, color=TEXT_MUTED, font_family="Inter"),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=1, color=BORDER_SUBTLE),
                    ft.Row(
                        controls=[
                            ft.Column(controls=[
                                ft.Text(str(campaign["total_found"]), size=22,
                                       weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                                ft.Text("Encontrados", size=10, color=TEXT_MUTED, font_family="Inter"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Column(controls=[
                                ft.Text(str(campaign["total_approved"]), size=22,
                                       weight=ft.FontWeight.W_700, color=SUCCESS, font_family="Inter"),
                                ft.Text("Aprovados", size=10, color=TEXT_MUTED, font_family="Inter"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Column(controls=[
                                ft.Text(str(campaign["total_discarded"]), size=22,
                                       weight=ft.FontWeight.W_700, color=ERROR, font_family="Inter"),
                                ft.Text("Descartados", size=10, color=TEXT_MUTED, font_family="Inter"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                ],
                spacing=10,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_SUBTLE),
            border_radius=14,
            padding=20,
        )

        # Lista de leads
        lead_items = []
        for i, lead in enumerate(leads):
            tags = lead.get("tags", [])
            if isinstance(tags, str):
                try:
                    import json
                    tags = json.loads(tags)
                except:
                    tags = []

            score = lead.get("score", 0)
            score_color = SUCCESS if score >= 8 else (WARNING if score >= 5 else ERROR)

            tag_chips = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(t, size=9, color=TAG_COLORS.get(t, "#6B7280"),
                                       weight=ft.FontWeight.W_600, font_family="Inter"),
                        bgcolor=f"{TAG_COLORS.get(t, '#6B7280')}15",
                        border=ft.Border.all(1, f"{TAG_COLORS.get(t, '#6B7280')}40"),
                        border_radius=16,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    )
                    for t in (tags[:3] if isinstance(tags, list) else [])
                ],
                spacing=4,
                wrap=True,
            )
            action_buttons = ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        icon_size=16,
                        icon_color=TEXT_SECONDARY,
                        tooltip="Abrir Site/Perfil",
                        url=lead.get("link", "") if lead.get("link") else None,
                    ),
                ],
                spacing=4,
            )

            if lead.get("whatsapp_ready") or lead.get("has_phone"):
                action_buttons.controls.append(
                    ft.IconButton(
                        icon=ft.Icons.CHAT,
                        icon_size=16,
                        icon_color=SUCCESS,
                        tooltip="WhatsApp",
                    )
                )

            lead_card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(f"{i+1}. {lead.get('name', '?')[:35]}",
                                       size=13, weight=ft.FontWeight.W_600,
                                       color=TEXT_PRIMARY, font_family="Inter"),
                                ft.Text(f"{score}/10", size=13, weight=ft.FontWeight.W_700,
                                       color=score_color, font_family="Inter"),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text(lead.get("reason", "")[:100], size=11, color=TEXT_SECONDARY,
                               font_family="Inter", max_lines=2),
                        ft.Row([tag_chips, action_buttons], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ],
                    spacing=6,
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=10,
                padding=14,
            )
            lead_items.append(lead_card)

        # Header com Botão de Exportar Excel
        export_btn = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FILE_DOWNLOAD, size=16),
                    ft.Text("EXPORTAR EXCEL", size=11, weight=ft.FontWeight.W_600),
                ],
                spacing=6,
            ),
            bgcolor=ACCENT,
            color=BG_PRIMARY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda e: export_to_excel(campaign, leads),
        )

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
        
        # Preparar dados para o Pandas
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
                "Descrição": lead.get("description", "")
            })
        
        df = pd.DataFrame(df_data)
        
        # Criar buffer em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads Aprovados')
        
        excel_data = output.getvalue()
        
        # Download (Híbrido)
        filename = f"Velli_Leads_{campaign['niche'].replace(' ', '_')}.xlsx"
        
        if page.web:
            # No Web usa Data URI
            b64 = base64.b64encode(excel_data).decode()
            page.launch_url(f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}")
        else:
            # No Desktop salva na Área de Trabalho
            import os
            path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            with open(path, "wb") as f:
                f.write(excel_data)
            
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Excel salvo em: {path}"))
            page.snack_bar.open = True
            page.update()


    def delete_and_refresh(campaign_id):
        """Deleta uma campanha e recarrega a lista."""
        delete_campaign(campaign_id)
        load_campaigns()

    def load_campaigns():
        """Carrega as campanhas (Isolado se Web)."""
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
                                        ft.Text(f"{c['total_approved']} leads", size=11,
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

    # Carregar ao construir
    load_campaigns()

    view_col = ft.Column(
        controls=[
            # Header
            ft.Row(
                controls=[
                    back_button,
                    ft.Column(
                        controls=[
                            ft.Text("Campanhas", size=24, weight=ft.FontWeight.W_700,
                                   color=TEXT_PRIMARY, font_family="Inter"),
                            ft.Text("Histórico completo de prospecções salvas",
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

            # Conteúdo
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


    # Expositor de atualização automática para cross-routing
    view.on_active = lambda: load_campaigns()

    return view
