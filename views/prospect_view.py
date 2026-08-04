import flet as ft
import threading
import time
import base64
import traceback
import json
from scraper import scrape_leads, get_available_sources
from ai_evaluator import evaluate_leads_batch
from database import update_campaign_stats
from persistence import save_campaign, add_lead_to_campaign
from views.copilot_view import build_copilot_view

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

def _build_metric_card(icon, value, label, color):
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(icon, size=16, color=color),
                        ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY, font_family="Inter"),
                    ],
                    spacing=6,
                ),
                ft.Text(str(value), size=24, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY, font_family="Inter"),
            ],
            spacing=4,
        ),
        bgcolor=BG_CARD,
        border=ft.Border.all(1, BORDER_SUBTLE),
        border_radius=12,
        padding=ft.Padding.all(16),
        expand=True,
    )

def _build_tag_chip(tag_text):
    color = TAG_COLORS.get(tag_text, "#888888")
    return ft.Container(
        content=ft.Text(tag_text.upper(), size=9, weight=ft.FontWeight.W_700, color=color, font_family="Inter"),
        bgcolor=f"{color}15",
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border_radius=4,
    )

def _build_lead_card(lead, index):
    score = int(lead.get("score", 0))
    if score >= 8:
        score_color = SUCCESS
    elif score >= 5:
        score_color = WARNING
    else:
        score_color = ERROR

    tags_row = ft.Row([_build_tag_chip(t) for t in lead.get("tags", [])], wrap=True, spacing=4)

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(str(score), size=14, weight=ft.FontWeight.W_800, color=BG_PRIMARY, font_family="Inter"),
                            bgcolor=score_color,
                            width=28,
                            height=28,
                            border_radius=14,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(lead.get("name", "N/A"), size=14, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                                ft.Text(lead.get("link", ""), size=11, color=TEXT_SECONDARY, font_family="Inter", selectable=True),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.COPY,
                            icon_size=16,
                            icon_color=TEXT_MUTED,
                            tooltip="Copiar Link",
                        ),
                    ],
                ),
                ft.Container(height=4),
                tags_row,
                ft.Container(height=4),
                ft.Text(f"\"{lead.get('reason', '')}\"", size=12, color=TEXT_MUTED, font_family="Inter", italic=True),
            ],
            spacing=0,
        ),
        bgcolor=BG_CARD,
        border=ft.Border.all(1, BORDER_SUBTLE),
        border_radius=12,
        padding=ft.Padding.all(16),
        margin=ft.Margin.only(bottom=10),
    )

def build_prospect_view(page: ft.Page):
    from database import get_setting
    
    niche_field = ft.TextField(label="Nicho (ex: Dentistas)", expand=True, border_color=BORDER_SUBTLE, focused_border_color=ACCENT, text_style=ft.TextStyle(font_family="Inter", size=14, color=TEXT_PRIMARY))
    region_field = ft.TextField(label="Regiao (ex: Sao Paulo)", expand=True, border_color=BORDER_SUBTLE, focused_border_color=ACCENT, text_style=ft.TextStyle(font_family="Inter", size=14, color=TEXT_PRIMARY))
    source_dropdown = ft.Dropdown(
        label="Canal de Busca",
        options=[ft.dropdown.Option(s) for s in get_available_sources()],
        value="Todas as Fontes",
        expand=True, border_color=BORDER_SUBTLE, focused_border_color=ACCENT, text_style=ft.TextStyle(font_family="Inter", size=14, color=TEXT_PRIMARY)
    )
    
    criteria_field = ft.TextField(
        label="Criterios de Qualificacao (IA)",
        multiline=True,
        min_lines=2,
        max_lines=4,
        value="Busque negocios premium, que ja investem em marketing ou tem grande potencial de melhoria. Evite franquias se possivel.",
        border_color=BORDER_SUBTLE, focused_border_color=ACCENT, text_style=ft.TextStyle(font_family="Inter", size=14, color=TEXT_PRIMARY)
    )

    min_score_slider = ft.Slider(min=1, max=10, divisions=9, value=5, label="Nota Minima: {value}")
    max_results_field = ft.TextField(label="Max Resultados", value="50", width=120, border_color=BORDER_SUBTLE, focused_border_color=ACCENT, text_style=ft.TextStyle(font_family="Inter", size=14, color=TEXT_PRIMARY))
    
    require_contact = ft.Checkbox(label="Exigir Telefone/Email", value=False)
    block_portals = ft.Checkbox(label="Ignorar Grandes Portais", value=True)

    progress_bar = ft.ProgressBar(width=400, color=ACCENT, bgcolor=BG_CARD, value=0, visible=False)
    status_text = ft.Text("", size=12, color=TEXT_SECONDARY, font_family="Inter", text_align=ft.TextAlign.CENTER)

    leads_list = ft.ListView(expand=True, spacing=10)
    
    total_lidos = ft.Text("0", size=24, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY, font_family="Inter")
    total_aprovados = ft.Text("0", size=24, weight=ft.FontWeight.W_800, color=SUCCESS, font_family="Inter")
    total_descartados = ft.Text("0", size=24, weight=ft.FontWeight.W_800, color=ERROR, font_family="Inter")

    metrics_row = ft.Row([
        _build_metric_card(ft.Icons.SEARCH, total_lidos.value, "Lidos", ACCENT),
        _build_metric_card(ft.Icons.CHECK_CIRCLE, total_aprovados.value, "Aprovados", SUCCESS),
        _build_metric_card(ft.Icons.CANCEL, total_descartados.value, "Descartados", ERROR),
    ], spacing=15, visible=False)

    filter_type = ft.Dropdown(
        options=[
            ft.dropdown.Option("Todos"),
            ft.dropdown.Option("B2B"),
            ft.dropdown.Option("B2C"),
            ft.dropdown.Option("E-commerce"),
            ft.dropdown.Option("Servico Local")
        ],
        value="Todos",
        width=150,
        height=35,
        text_size=12,
        border_color=BORDER_SUBTLE,
        bgcolor=BG_CARD
    )
    
    filter_tag = ft.Dropdown(
        options=[ft.dropdown.Option("Todas as Tags")] + [ft.dropdown.Option(t) for t in TAG_COLORS.keys()],
        value="Todas as Tags",
        width=150,
        height=35,
        text_size=12,
        border_color=BORDER_SUBTLE,
        bgcolor=BG_CARD
    )

    current_leads_data = []

    def apply_filters(e):
        leads_list.controls.clear()
        
        for ld in current_leads_data:
            t = filter_type.value
            if t != "Todos" and t not in ld.get("tags", []): continue
            
            tg = filter_tag.value
            if tg != "Todas as Tags" and tg not in ld.get("tags", []): continue
            
            leads_list.controls.append(_build_lead_card(ld, len(leads_list.controls)))
            
        page.update()

    filter_type.on_change = apply_filters
    filter_tag.on_change = apply_filters

    def start_prospection(e):
        niche = niche_field.value.strip()
        region = region_field.value.strip()
        
        if not niche or not region:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha Nicho e Regiao!"))
            page.snack_bar.open = True
            page.update()
            return
            
        api_key = get_setting("gemini_api_key", "")
        if not api_key:
            page.snack_bar = ft.SnackBar(ft.Text("Vá em Configuracoes e adicione a API Key do Gemini."))
            page.snack_bar.open = True
            page.update()
            return

        progress_bar.visible = True
        progress_bar.value = 0
        metrics_row.visible = True
        leads_list.controls.clear()
        current_leads_data.clear()
        
        total_lidos.value = "0"
        total_aprovados.value = "0"
        total_descartados.value = "0"
        
        metrics_row.controls[0].content.controls[1].value = "0"
        metrics_row.controls[1].content.controls[1].value = "0"
        metrics_row.controls[2].content.controls[1].value = "0"

        def _run():
            try:
                status_text.value = f"Iniciando varredura para {niche} em {region}..."
                page.update()
                
                campaign_id = save_campaign(page, {
                    "name": f"{niche} em {region}",
                    "niche": niche,
                    "region": region,
                    "source": source_dropdown.value,
                    "criteria": criteria_field.value,
                    "min_score": int(min_score_slider.value),
                    "max_results": int(max_results_field.value)
                })

                def on_prog(current, total, name):
                    status_text.value = f"Extraindo dados ({current}/{total}): {name}..."
                    progress_bar.value = (current / total) * 0.3
                    page.update()

                scraped = scrape_leads(
                    niche=niche,
                    region=region,
                    source=source_dropdown.value,
                    max_results=int(max_results_field.value),
                    block_large_portals=block_portals.value,
                    on_progress=on_prog
                )
                
                if not scraped:
                    status_text.value = "Nenhum resultado encontrado pelo motor de busca. Tente alterar os termos."
                    update_campaign_stats(campaign_id, 0, 0, 0, "failed")
                    progress_bar.visible = False
                    page.update()
                    return

                metrics_row.controls[0].content.controls[1].value = str(len(scraped))
                page.update()

                filtered = []
                for s in scraped:
                    if require_contact.value and not s.get("_has_contact", False):
                        continue
                    filtered.append(s)
                
                discarded_contact = len(scraped) - len(filtered)
                if discarded_contact > 0:
                    status_text.value = f"{discarded_contact} leads descartados por falta de contato. Avaliando {len(filtered)}..."
                    metrics_row.controls[2].content.controls[1].value = str(discarded_contact)
                    page.update()
                    time.sleep(2)

                if not filtered:
                    status_text.value = "Todos os leads foram filtrados (nenhum possuia contato publico)."
                    update_campaign_stats(campaign_id, len(scraped), 0, len(scraped), "completed")
                    progress_bar.visible = False
                    page.update()
                    return

                batch_size = 10
                approved_count = 0
                discarded_ai = 0
                
                for i in range(0, len(filtered), batch_size):
                    batch = filtered[i:i+batch_size]
                    
                    status_text.value = f"Avaliando lote {i//batch_size + 1}... ({i}/{len(filtered)})"
                    progress_bar.value = 0.3 + (i / len(filtered)) * 0.7
                    page.update()

                    results = evaluate_leads_batch(batch, api_key, criteria_field.value)
                    
                    for j, res in enumerate(results):
                        lead = batch[j]
                        score = res.get("score", 0)
                        
                        if score >= int(min_score_slider.value):
                            lead_data = {
                                "name": lead.get("Nome"),
                                "link": lead.get("Link"),
                                "description": lead.get("Descricao (Bio/Web)"),
                                "has_phone": lead.get("Tem Telefone?") == "Sim",
                                "has_email": lead.get("Tem E-mail?") == "Sim",
                                "score": score,
                                "reason": res.get("reason", ""),
                                "tags": res.get("tags", []),
                                "decision_maker": res.get("decision_maker", ""),
                                "whatsapp_ready": res.get("whatsapp_ready", False)
                            }
                            
                            add_lead_to_campaign(page, campaign_id, lead_data)
                            current_leads_data.append(lead_data)
                            leads_list.controls.append(_build_lead_card(lead_data, len(leads_list.controls)))
                            approved_count += 1
                        else:
                            discarded_ai += 1
                            
                    metrics_row.controls[1].content.controls[1].value = str(approved_count)
                    metrics_row.controls[2].content.controls[1].value = str(discarded_contact + discarded_ai)
                    page.update()
                    
                    if i + batch_size < len(filtered):
                        time.sleep(1) 

                status_text.value = f"Busca concluida! {approved_count} aprovados."
                progress_bar.value = 1.0
                update_campaign_stats(campaign_id, len(scraped), approved_count, discarded_contact + discarded_ai, "completed")
                
            except Exception as ex:
                err = traceback.format_exc()
                print(err)
                status_text.value = f"ERRO CRITICO: {ex}"
                status_text.color = ERROR
                progress_bar.color = ERROR
                
            progress_bar.visible = False
            page.update()

        threading.Thread(target=_run, daemon=True).start()

    btn_start = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.ROCKET_LAUNCH, size=16, color=BG_PRIMARY),
            ft.Text("INICIAR PROSPECCAO", size=13, weight=ft.FontWeight.W_700, color=BG_PRIMARY, font_family="Inter"),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ACCENT,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding.symmetric(vertical=16, horizontal=24),
            elevation=0,
        ),
        on_click=start_prospection,
    )

    view_content = ft.Column(
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Text("Nova Prospeccao", size=24, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                    ft.Text("Configure os filtros para a IA encontrar os melhores clientes.", size=13, color=TEXT_SECONDARY, font_family="Inter"),
                ], spacing=4),
                padding=ft.Padding.only(bottom=20),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([niche_field, region_field], spacing=15),
                    ft.Row([source_dropdown, max_results_field], spacing=15),
                    ft.Row([require_contact, block_portals], spacing=15),
                    criteria_field,
                    min_score_slider,
                    ft.Container(height=8),
                    btn_start,
                ], spacing=12),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=14,
                padding=24,
            ),
            ft.Container(height=16),
            ft.Column([
                progress_bar,
                status_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            metrics_row,
            ft.Container(height=16),
            ft.Row([
                ft.Text("Leads Aprovados", size=18, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                ft.Container(expand=True),
                filter_type,
                filter_tag
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            leads_list
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    drawer = ft.Container(
        content=build_copilot_view(page),
        width=400,
        bgcolor=BG_PRIMARY,
        border=ft.border.only(left=ft.BorderSide(1, BORDER_SUBTLE)),
        right=-400,
        top=0,
        bottom=0,
        animate_position=300
    )

    overlay = ft.Container(
        bgcolor=ft.colors.with_opacity(0.5, "#000000"),
        expand=True,
        visible=False,
        on_click=lambda e: toggle_drawer()
    )

    is_drawer_open = False
    def toggle_drawer(e=None):
        nonlocal is_drawer_open
        is_drawer_open = not is_drawer_open
        drawer.right = 0 if is_drawer_open else -400
        overlay.visible = is_drawer_open
        page.update()

    fab = ft.FloatingActionButton(
        content=ft.Row([
            ft.Icon(ft.Icons.SMART_TOY, color=BG_PRIMARY),
            ft.Text("VELLIX IA", size=14, weight=ft.FontWeight.W_800, color=BG_PRIMARY, font_family="Inter")
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
        bgcolor=ACCENT,
        shape=ft.RoundedRectangleBorder(radius=30),
        width=140,
        on_click=toggle_drawer
    )

    return ft.Stack([
        ft.Container(
            content=view_content,
            padding=ft.Padding.symmetric(horizontal=24, vertical=20),
            expand=True,
        ),
        overlay,
        drawer,
        ft.Container(content=fab, right=20, bottom=20)
    ], expand=True)