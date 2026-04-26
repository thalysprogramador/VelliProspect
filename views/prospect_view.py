"""
Velli Prospect V3 — Prospect View
Tela principal de configuração e execução de prospecção.
"""
import flet as ft
import threading
import time
from scraper import scrape_leads, get_available_sources
from ai_evaluator import evaluate_lead, evaluate_leads_batch
from database import create_campaign, update_campaign_stats, insert_lead
from views.copilot_view import build_copilot_view


# ─── Cores do Design System B&W ─────────────────────────────
BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BG_CARD_HOVER = "#1C1C1C"
BORDER_SUBTLE = "#2A2A2A"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
ACCENT_DIM = "#CCCCCC"
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


def _build_metric_card(icon, value, label, color=TEXT_PRIMARY):
    """Cria um card de métrica minimalista."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(icon, size=20, color=TEXT_SECONDARY),
                ft.Text(str(value), size=28, weight=ft.FontWeight.W_700, color=color, 
                        font_family="Inter"),
                ft.Text(label, size=11, color=TEXT_SECONDARY, font_family="Inter"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        bgcolor=BG_CARD,
        border=ft.Border.all(1, BORDER_SUBTLE),
        border_radius=12,
        padding=ft.Padding.symmetric(vertical=16, horizontal=20),
        expand=True,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
    )


def _build_tag_chip(tag_text):
    """Cria um chip de tag colorido."""
    color = TAG_COLORS.get(tag_text, "#6B7280")
    return ft.Container(
        content=ft.Text(tag_text, size=10, color=color, weight=ft.FontWeight.W_600, 
                        font_family="Inter"),
        bgcolor=f"{color}15",
        border=ft.Border.all(1, f"{color}40"),
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )


def _build_lead_card(lead, index, on_whatsapp=None):
    """Cria o card visual de um lead aprovado."""
    score = lead.get("score", 0)
    tags = lead.get("tags", [])
    if isinstance(tags, str):
        try:
            import json
            tags = json.loads(tags)
        except:
            tags = []

    # Cor do score
    if score >= 8:
        score_color = SUCCESS
        score_icon = ft.Icons.ROCKET_LAUNCH
    elif score >= 5:
        score_color = WARNING
        score_icon = ft.Icons.TRENDING_UP
    else:
        score_color = ERROR
        score_icon = ft.Icons.TRENDING_DOWN

    tag_row = ft.Row(
        controls=[_build_tag_chip(t) for t in tags[:4]],
        spacing=6,
        wrap=True
    )

    # Botões de ação
    action_buttons = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.OPEN_IN_NEW,
                icon_size=16,
                icon_color=TEXT_SECONDARY,
                tooltip="Abrir Link",
                url=lead.get("link", ""),
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
                on_click=on_whatsapp if on_whatsapp else None,
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                # Header: Nome + Score
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(str(index + 1), size=11, 
                                                    color=TEXT_MUTED, weight=ft.FontWeight.W_600,
                                                    font_family="Inter"),
                                    bgcolor="#1F1F1F",
                                    border_radius=6,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                ),
                                ft.Text(
                                    lead.get("name", "Desconhecido")[:40],
                                    size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY,
                                    font_family="Inter",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(score_icon, size=16, color=score_color),
                                ft.Text(f"{score}/10", size=14, weight=ft.FontWeight.W_700,
                                        color=score_color, font_family="Inter"),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # Descrição
                ft.Text(
                    lead.get("reason", lead.get("description", ""))[:120],
                    size=12, color=TEXT_SECONDARY, font_family="Inter",
                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                ),
                # Tags
                tag_row,
                # Footer: decisor + ações
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PERSON_OUTLINE, size=14, color=TEXT_MUTED),
                                ft.Text(
                                    lead.get("decision_maker", "Desconhecido"),
                                    size=11, color=TEXT_MUTED, font_family="Inter"
                                ),
                            ],
                            spacing=4,
                        ),
                        action_buttons,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=10,
        ),
        bgcolor=BG_CARD,
        border=ft.Border.all(1, BORDER_SUBTLE),
        border_radius=12,
        padding=16,
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        offset=ft.Offset(0, 0),
        animate_offset=ft.Animation(500, ft.AnimationCurve.DECELERATE),
    )


def build_prospect_view(page: ft.Page):
    """Constrói e retorna a view de prospecção."""

    # ─── State ────────────────────────────────────────────
    approved_leads = []
    is_running = False

    # ─── Refs da UI ───────────────────────────────────────
    niche_field = ft.TextField(
        label="Nicho de Mercado",
        hint_text="Ex: Clínica de Estética, Escritório de Advocacia...",
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=10,
        filled=True,
        fill_color=BG_CARD,
    )

    region_field = ft.TextField(
        label="Região / Cidade",
        hint_text="Ex: São Paulo, Belo Horizonte...",
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=10,
        filled=True,
        fill_color=BG_CARD,
    )

    source_dropdown = ft.Dropdown(
        label="Fonte de Busca",
        options=[ft.dropdown.Option(s) for s in get_available_sources()],
        value="Instagram",
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=10,
        filled=True,
        fill_color=BG_CARD,
    )

    criteria_field = ft.TextField(
        label="Instruções para a IA (Personalizado)",
        hint_text="Descreva o perfil ideal de cliente...",
        value="Procure empresas que parecem pequenas ou não têm site profissional. Exclua franquias gigantes.",
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=10,
        filled=True,
        fill_color=BG_CARD,
    )

    min_score_slider = ft.Slider(
        min=1, max=10, divisions=9, value=7,
        label="{value}",
        active_color=ACCENT,
        inactive_color=BORDER_SUBTLE,
        thumb_color=ACCENT,
    )
    min_score_label = ft.Text("Nota Mínima: 7", size=12, color=TEXT_SECONDARY, font_family="Inter")

    def on_slider_change(e):
        min_score_label.value = f"Nota Mínima: {int(e.control.value)}"
        page.update()

    min_score_slider.on_change = on_slider_change

    max_results_field = ft.TextField(
        label="Quantidade de Leads",
        value="100",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=10,
        filled=True,
        fill_color=BG_CARD,
        suffix=ft.Text("máx: 1000"),
        suffix_style=ft.TextStyle(color=TEXT_MUTED, size=10),
    )

    require_contact = ft.Checkbox(
        label="Exigir telefone ou e-mail visível",
        value=False,
        check_color=BG_PRIMARY,
        fill_color={
            ft.ControlState.SELECTED: ACCENT,
            ft.ControlState.DEFAULT: "transparent",
        },
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12, font_family="Inter"),
    )

    block_portals = ft.Checkbox(
        label="Bloquear grandes portais (G1, OLX, etc)",
        value=True,
        check_color=BG_PRIMARY,
        fill_color={
            ft.ControlState.SELECTED: ACCENT,
            ft.ControlState.DEFAULT: "transparent",
        },
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12, font_family="Inter"),
    )

    # ─── Área de progresso e resultados ───────────────────
    progress_bar = ft.ProgressBar(
        value=0, bgcolor=BORDER_SUBTLE, color=ACCENT, bar_height=3,
        border_radius=2, visible=False,
    )
    status_text = ft.Text(
        "", size=12, color=TEXT_SECONDARY, font_family="Inter",
        italic=True, visible=False,
    )

    # Métricas
    metric_found = ft.Ref[ft.Text]()
    metric_approved = ft.Ref[ft.Text]()
    metric_discarded = ft.Ref[ft.Text]()

    metrics_row = ft.Row(
        controls=[
            _build_metric_card(ft.Icons.SEARCH, "0", "Perfis Lidos"),
            _build_metric_card(ft.Icons.STAR, "0", "Aprovados", SUCCESS),
            _build_metric_card(ft.Icons.DELETE_OUTLINE, "0", "Descartados", ERROR),
        ],
        spacing=12,
        visible=False,
    )

    # Lista de leads
    leads_list = ft.ListView(
        spacing=10,
        padding=ft.Padding.only(top=10),
        auto_scroll=True,
        expand=True,
    )

    leads_container = ft.Container(
        content=leads_list,
        expand=True,
        visible=False,
    )

    # Botão principal
    run_button = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ROCKET_LAUNCH, color=BG_PRIMARY, size=18),
                    ft.Text("EXECUTAR VARREDURA", size=14, weight=ft.FontWeight.W_700,
                            color=BG_PRIMARY, font_family="Inter"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=ACCENT,
            color=BG_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding.symmetric(vertical=16, horizontal=32),
                elevation=0,
                animation_duration=200,
            ),
            on_click=lambda e: start_prospection(e),
        ),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
    )

    # Download button
    download_button = ft.ElevatedButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.DOWNLOAD, color=BG_PRIMARY, size=16),
                ft.Text("EXPORTAR CSV", size=12, weight=ft.FontWeight.W_600,
                        color=BG_PRIMARY, font_family="Inter"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        bgcolor="#333333",
        color=TEXT_PRIMARY,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding.symmetric(vertical=12, horizontal=20),
            elevation=0,
        ),
        visible=False,
        on_click=lambda e: export_csv(e),
    )

    def export_csv(e):
        """Exporta leads aprovados para CSV."""
        if not approved_leads:
            return
        import csv
        import io
        import os

        # Gerar CSV em memória
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "link", "description", "score", 
                                                       "reason", "tags", "decision_maker"])
        writer.writeheader()
        for lead in approved_leads:
            row = {k: lead.get(k, "") for k in writer.fieldnames}
            if isinstance(row.get("tags"), list):
                row["tags"] = ", ".join(row["tags"])
            writer.writerow(row)

        csv_content = output.getvalue()

        # Salvar arquivo
        save_path = os.path.join(os.path.expanduser("~"), "Desktop", "Velli_Leads_Premium.csv")
        try:
            with open(save_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(csv_content)
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ Salvo em: {save_path}", color=TEXT_PRIMARY, font_family="Inter"),
                bgcolor=BG_CARD,
            )
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao salvar: {ex}", color=ERROR, font_family="Inter"),
                bgcolor=BG_CARD,
            )
            page.snack_bar.open = True
            page.update()

    def start_prospection(e):
        """Inicia o processo de prospecção em thread separada."""
        nonlocal is_running, approved_leads

        if is_running:
            return

        from database import get_setting
        # Prioriza a chave do navegador (isolamento multi-usuário na Web)
        api_key = ""
        if page.web:
            api_key = page.client_storage.get("gemini_api_key")
        
        if not api_key:
            api_key = get_setting("gemini_api_key")

        niche = niche_field.value
        region = region_field.value
        source = source_dropdown.value

        if not niche or not region:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("⚠️ Preencha o Nicho e a Região.", color=WARNING, font_family="Inter"),
                bgcolor=BG_CARD,
            )
            page.snack_bar.open = True
            page.update()
            return

        if not api_key:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("⚠️ Configure sua API Key do Gemini em ⚙️ Configurações.", 
                               color=WARNING, font_family="Inter"),
                bgcolor=BG_CARD,
            )
            page.snack_bar.open = True
            page.update()
            return

        is_running = True
        run_button.content.disabled = True
        approved_leads = []

        # Limpar resultados anteriores
        leads_list.controls.clear()
        progress_bar.visible = True
        progress_bar.value = 0
        status_text.visible = True
        status_text.value = "🔍 Iniciando varredura na internet..."
        metrics_row.visible = True
        leads_container.visible = True
        download_button.visible = False
        page.update()

        max_r = min(int(max_results_field.value or "100"), 1000)
        min_s = int(min_score_slider.value)
        criteria = criteria_field.value

        # Thread para não travar a UI
        def run_in_background():
            nonlocal approved_leads, is_running
            
            try:
                campaign_id = create_campaign(
                    name=f"{niche} — {region}",
                    niche=niche,
                    region=region,
                    source=source,
                    criteria=criteria,
                    min_score=min_s,
                    max_results=max_r,
                )

                # Fase 1: Scraping
                status_text.value = f"🌐 Vasculhando '{source}' em '{region}'..."
                page.update()

                raw_leads = scrape_leads(
                    niche, region, source,
                    max_results=max_r,
                    block_large_portals=block_portals.value,
                )

                if not raw_leads:
                    status_text.value = "⚠️ Nenhum resultado encontrado. Tente termos diferentes."
                    progress_bar.visible = False
                    update_campaign_stats(campaign_id, 0, 0, 0, "empty")
                    return

                # Atualizar métrica "Perfis Lidos"
                found_card = metrics_row.controls[0]
                found_card.content.controls[1].value = str(len(raw_leads))
                page.update()

                # Fase 2: Avaliação pela IA (Em Lote)
                discarded = 0
                total_leads = len(raw_leads)
                batch_size = 20
                
                for batch_start in range(0, total_leads, batch_size):
                    if not is_running:
                        break
                        
                    batch_leads = raw_leads[batch_start:batch_start+batch_size]
                    end_idx = min(batch_start+batch_size, total_leads)
                    
                    status_text.value = f"🤖 VELLIX IA processando em lote super-rápido: {batch_start+1} a {end_idx} de {total_leads} leads..."
                    page.update()
                    
                    batch_results = evaluate_leads_batch(batch_leads, api_key, criteria)
                    
                    for i, lead in enumerate(batch_leads):
                        progress = (batch_start + i + 1) / total_leads
                        progress_bar.value = progress
                        
                        # Filtro rápido
                        if require_contact.value and not lead['_has_contact']:
                            discarded += 1
                            metrics_row.controls[2].content.controls[1].value = str(discarded)
                            continue
                            
                        result = batch_results[i] if i < len(batch_results) else {"score": 0, "reason": "Falha na IA."}
                        
                        if int(result.get("score", 0)) >= min_s:
                            enriched_lead = {
                                "name": lead["Nome"],
                                "link": lead["Link"],
                                "description": lead["Descrição (Bio/Web)"],
                                "has_phone": lead.get("Tem Telefone?") == "Sim",
                                "has_email": lead.get("Tem E-mail?") == "Sim",
                                **result
                            }
                            approved_leads.append(enriched_lead)

                            # Salvar no banco
                            insert_lead(campaign_id, enriched_lead)

                            # Adicionar card na lista com animação
                            card = _build_lead_card(enriched_lead, len(approved_leads) - 1)
                            leads_list.controls.append(card)

                            # Atualizar métrica "Aprovados"
                            metrics_row.controls[1].content.controls[1].value = str(len(approved_leads))
                        else:
                            discarded += 1
                            metrics_row.controls[2].content.controls[1].value = str(discarded)
                            
                        # Atualiza a UI a cada lead inserido visualmente
                        page.update()

                # Finalizar
                update_campaign_stats(campaign_id, len(raw_leads), len(approved_leads), discarded)

                status_text.value = f"✅ Varredura concluída! {len(approved_leads)} leads aprovados de {len(raw_leads)} perfis."
                progress_bar.visible = False
                download_button.visible = len(approved_leads) > 0

            except Exception as e:
                status_text.value = f"❌ Erro na varredura: {e}"
                progress_bar.visible = False
            finally:
                is_running = False
                run_button.content.disabled = False
                page.update()

        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()

    view_main = ft.Column(
        controls=[
            # Header
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Nova Prospecção", size=24, weight=ft.FontWeight.W_700,
                               color=TEXT_PRIMARY, font_family="Inter"),
                        ft.Text("Configure e execute uma varredura inteligente de leads",
                               size=13, color=TEXT_SECONDARY, font_family="Inter"),
                    ],
                    spacing=4,
                ),
                padding=ft.Padding.only(bottom=20),
            ),


            # Seção 1: Onde e Quem
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.LOCATION_SEARCHING, size=16, color=TEXT_SECONDARY),
                                ft.Text("ALVO", size=11, weight=ft.FontWeight.W_600,
                                        color=TEXT_SECONDARY, font_family="Inter"),
                            ],
                            spacing=8,
                        ),
                        ft.ResponsiveRow(
                            controls=[
                                ft.Column(col={"sm": 12, "md": 4}, controls=[niche_field]),
                                ft.Column(col={"sm": 12, "md": 4}, controls=[region_field]),
                                ft.Column(col={"sm": 12, "md": 4}, controls=[source_dropdown]),
                            ],
                        ),
                    ],
                    spacing=12,
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=14,
                padding=20,
            ),

            ft.Container(height=12),

            # Seção 2: Inteligência
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PSYCHOLOGY, size=16, color=TEXT_SECONDARY),
                                ft.Text("INTELIGÊNCIA", size=11, weight=ft.FontWeight.W_600,
                                        color=TEXT_SECONDARY, font_family="Inter"),
                            ],
                            spacing=8,
                        ),
                        criteria_field,
                        ft.ResponsiveRow(
                            controls=[
                                ft.Column(col={"sm": 12, "md": 4}, controls=[
                                    ft.Column(controls=[min_score_label, min_score_slider], spacing=4),
                                ]),
                                ft.Column(col={"sm": 12, "md": 4}, controls=[max_results_field]),
                                ft.Column(col={"sm": 12, "md": 4}, controls=[
                                    ft.Column(controls=[require_contact, block_portals], spacing=4),
                                ]),
                            ],
                        ),
                    ],
                    spacing=12,
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=14,
                padding=20,
            ),

            ft.Container(height=16),

            # Botão principal
            ft.Row(
                controls=[run_button, download_button],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),

            ft.Container(height=12),

            # Progresso
            progress_bar,
            status_text,

            ft.Container(height=8),

            # Métricas
            metrics_row,

            ft.Container(height=8),

            # Leads
            leads_container,
            ft.Container(height=80), # Espaço para o FAB não cobrir conteúdo
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
    )
    
    view = ft.Container(
        content=view_main,
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        expand=True,
    )

    # ─── VELLIX IA Drawer ───────────────────────────────────
    copilot_ui = build_copilot_view(page)
    # Ajuste de layout para caber na gaveta
    if hasattr(copilot_ui, "controls") and len(copilot_ui.controls) > 0:
        copilot_ui.controls[0].padding = ft.Padding.only(bottom=10)

    drawer = ft.Container(
        content=copilot_ui,
        width=420,
        bgcolor=BG_CARD,
        border=ft.Border(left=ft.BorderSide(1, BORDER_SUBTLE)),
        right=-430, # Escondido à direita
        top=0,
        bottom=0,
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=50, color="#88000000"),
        animate=ft.Animation(500, ft.AnimationCurve.DECELERATE),
    )

    overlay = ft.Container(
        expand=True,
        bgcolor="#33000000",
        blur=ft.Blur(10, 10, ft.BlurTileMode.CLAMP),
        visible=False,
        opacity=0,
        on_click=lambda _: toggle_copilot(None),
        animate_opacity=300,
    )

    def toggle_copilot(e):
        if drawer.right == -430:
            overlay.visible = True
            page.update() # Garante que visible=True antes da opacidade
            drawer.right = 0
            overlay.opacity = 1
        else:
            drawer.right = -430
            overlay.opacity = 0
            page.update()
            import time
            def hide_overlay():
                time.sleep(0.3)
                overlay.visible = False
                page.update()
            threading.Thread(target=hide_overlay, daemon=True).start()
        page.update()

    fab = ft.Container(
        content=ft.FloatingActionButton(
            content=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, size=18), ft.Text("VELLIX IA", weight=ft.FontWeight.W_700, font_family="Inter")], spacing=4),
            bgcolor=ACCENT,
            foreground_color=BG_PRIMARY,
            on_click=toggle_copilot,
            width=130,
        ),
        right=24,
        bottom=24,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
    )

    stack = ft.Stack(
        controls=[
            view,
            overlay,
            fab,
            drawer,
        ],
        expand=True,
    )

    return stack
