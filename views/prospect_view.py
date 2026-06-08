"""
Velli Prospect V3 — Prospect View (Revisado)
Tela principal de configuracao, execucao de prospeccao e filtros de segmentacao.
"""
import flet as ft
import threading
import time
import base64
from scraper import scrape_leads, get_available_sources
from ai_evaluator import evaluate_lead, evaluate_leads_batch
from database import update_campaign_stats
from persistence import get_campaigns, save_campaign, add_lead_to_campaign
from views.copilot_view import build_copilot_view


# Design System
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
    "Boa Presenca Digital": "#3B82F6",
    "Baixa Presenca Digital": "#F59E0B",
    "Franquia / Rede": "#8B5CF6",
    "Novo no Mercado": "#06B6D4",
    "Decisor Acessivel": "#10B981",
    "Alta Concorrencia": "#F43F5E",
    "Oportunidade Urgente": "#E11D48",
    "E-commerce": "#8B5CF6",
    "Servico Local": "#0EA5E9",
    "B2B": "#14B8A6",
    "B2C": "#F43F5E",
    "Alto Potencial Digital": "#8B5CF6",
    "Tem Redes Sociais": "#3B82F6",
    "Erro": "#6B7280",
    "Erro de API": "#EF4444",
}


def _build_metric_card(icon, value, label, color=TEXT_PRIMARY):
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
    )


def _build_tag_chip(tag_text):
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
    score = lead.get("score", 0)
    tags = lead.get("tags", [])
    if isinstance(tags, str):
        try:
            import json
            tags = json.loads(tags)
        except:
            tags = []

    if score >= 8:
        score_color = SUCCESS
        score_icon = ft.Icons.ROCKET_LAUNCH
    elif score >= 5:
        score_color = WARNING
        score_icon = ft.Icons.TRENDING_UP
    else:
        score_color = ERROR
        score_icon = ft.Icons.TRENDING_DOWN

    tag_row = ft.Row([_build_tag_chip(t) for t in tags[:4]], spacing=6, wrap=True)

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
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(str(index + 1), size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
                                    bgcolor="#1F1F1F", border_radius=6, padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                ),
                                ft.Text(lead.get("name", "Desconhecido")[:40], size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(score_icon, size=16, color=score_color),
                                ft.Text(f"{score}/10", size=14, weight=ft.FontWeight.W_700, color=score_color),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
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
    )


def build_prospect_view(page: ft.Page):
    """Constroi e retorna a view de prospeccao."""

    approved_leads = []
    is_running = False

    niche_field = ft.TextField(
        label="Nicho de Mercado",
        hint_text="Ex: Clinica de Estetica...",
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
        label="Regiao / Cidade",
        hint_text="Ex: Sao Paulo...",
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
        value="Todas as Fontes",
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
        label="Instrucoes para a IA (Personalizado)",
        value="Procure empresas que parecem pequenas ou nao tem site profissional. Exclua franquias.",
        multiline=True,
        min_lines=3,
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
    min_score_label = ft.Text("Nota Minima: 7", size=12, color=TEXT_SECONDARY, font_family="Inter")

    def on_slider_change(e):
        min_score_label.value = f"Nota Minima: {int(e.control.value)}"
        page.update()

    min_score_slider.on_change = on_slider_change

    max_results_field = ft.TextField(
        label="Quantidade de Leads",
        value="50",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=10,
        filled=True,
        fill_color=BG_CARD,
    )

    require_contact = ft.Checkbox(
        label="Exigir telefone/e-mail",
        value=True,
        fill_color={ft.ControlState.SELECTED: ACCENT, ft.ControlState.DEFAULT: "transparent"},
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12, font_family="Inter"),
    )

    block_portals = ft.Checkbox(
        label="Bloquear portais",
        value=True,
        fill_color={ft.ControlState.SELECTED: ACCENT, ft.ControlState.DEFAULT: "transparent"},
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12, font_family="Inter"),
    )

    progress_bar = ft.ProgressBar(value=0, bgcolor=BORDER_SUBTLE, color=ACCENT, bar_height=3, visible=False)
    status_text = ft.Text("", size=12, color=TEXT_SECONDARY, font_family="Inter", italic=True, visible=False)

    metrics_row = ft.Row(
        controls=[
            _build_metric_card(ft.Icons.SEARCH, "0", "Perfis Lidos"),
            _build_metric_card(ft.Icons.STAR, "0", "Aprovados", SUCCESS),
            _build_metric_card(ft.Icons.DELETE_OUTLINE, "0", "Descartados", ERROR),
        ],
        spacing=12,
        visible=False,
    )

    # Filtros visuais
    filter_type = ft.Dropdown(
        label="Tipo de Negocio",
        options=[
            ft.dropdown.Option("Todos"),
            ft.dropdown.Option("B2B"),
            ft.dropdown.Option("B2C"),
            ft.dropdown.Option("E-commerce"),
            ft.dropdown.Option("Servico Local")
        ],
        value="Todos",
        width=200,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        text_style=ft.TextStyle(font_family="Inter", size=12),
        label_style=ft.TextStyle(font_family="Inter", size=11),
        border_radius=8,
    )

    filter_tag = ft.Dropdown(
        label="Tag Especifica",
        options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(t) for t in TAG_COLORS.keys() if t != "Erro"],
        value="Todas",
        width=200,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        text_style=ft.TextStyle(font_family="Inter", size=12),
        label_style=ft.TextStyle(font_family="Inter", size=11),
        border_radius=8,
    )

    def apply_filters(e):
        tipo = filter_type.value
        tag = filter_tag.value

        visible_count = 0
        for card, lead in zip(leads_list.controls, approved_leads):
            lead_tags = lead.get("tags", [])
            show = True

            if tipo != "Todos" and tipo not in lead_tags:
                show = False
            if tag != "Todas" and tag not in lead_tags:
                show = False

            card.visible = show
            if show: visible_count += 1

        filter_status.value = f"Mostrando {visible_count} de {len(approved_leads)} leads."
        page.update()

    filter_type.on_change = apply_filters
    filter_tag.on_change = apply_filters
    filter_status = ft.Text("", size=11, color=TEXT_MUTED, font_family="Inter")

    filters_section = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.FILTER_LIST, size=16, color=TEXT_SECONDARY), ft.Text("FILTROS RÁPIDOS", size=11, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)]),
            ft.Row([filter_type, filter_tag]),
            filter_status
        ]),
        bgcolor=BG_CARD,
        border=ft.Border.all(1, BORDER_SUBTLE),
        border_radius=12,
        padding=16,
        visible=False
    )


    leads_list = ft.ListView(spacing=10, padding=ft.Padding.only(top=10), auto_scroll=False, expand=True)
    leads_container = ft.Container(content=leads_list, expand=True, visible=False)

    run_button = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row([ft.Icon(ft.Icons.ROCKET_LAUNCH, color=BG_PRIMARY, size=18), ft.Text("EXECUTAR VARREDURA", size=14, weight=ft.FontWeight.W_700, color=BG_PRIMARY)], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ACCENT,
            color=BG_PRIMARY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), padding=ft.Padding.symmetric(vertical=16, horizontal=32)),
            on_click=lambda e: start_prospection(e),
        )
    )

    def export_csv(e):
        if not approved_leads: return
        import csv
        import io

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "link", "description", "score", "reason", "tags", "decision_maker"])
        writer.writeheader()
        for lead in approved_leads:
            row = {k: lead.get(k, "") for k in writer.fieldnames}
            if isinstance(row.get("tags"), list):
                row["tags"] = ", ".join(row["tags"])
            writer.writerow(row)

        csv_content = output.getvalue()
        b64 = base64.b64encode(csv_content.encode("utf-8-sig")).decode()

        is_web = getattr(page, 'web', True)

        if is_web:
            page.launch_url(f"data:text/csv;base64,{b64}")
        else:
            import os
            save_path = os.path.join(os.path.expanduser("~"), "Desktop", "Velli_Leads.csv")
            try:
                with open(save_path, "w", encoding="utf-8-sig", newline="") as f:
                    f.write(csv_content)
                page.snack_bar = ft.SnackBar(ft.Text(f"Salvo em: {save_path}"))
                page.snack_bar.open = True
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {ex}"))
                page.snack_bar.open = True
            page.update()

    download_button = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.DOWNLOAD, color=BG_PRIMARY, size=16), ft.Text("EXPORTAR CSV", size=12, weight=ft.FontWeight.W_600, color=BG_PRIMARY)], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#333333", color=TEXT_PRIMARY, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        visible=False, on_click=export_csv,
    )

    def start_prospection(e):
        nonlocal is_running, approved_leads

        if is_running: return

        from database import get_setting
        import os
        api_key = os.environ.get("GEMINI_API_KEY") or get_setting("gemini_api_key")
        niche = niche_field.value
        region = region_field.value
        source = source_dropdown.value

        if not niche or not region:
            page.snack_bar = ft.SnackBar(content=ft.Text("Preencha Nicho e Regiao."))
            page.snack_bar.open = True
            page.update()
            return

        if not api_key:
            page.snack_bar = ft.SnackBar(content=ft.Text("Configure a API Key em Config."))
            page.snack_bar.open = True
            page.update()
            return

        is_running = True
        run_button.content.disabled = True
        approved_leads = []
        leads_list.controls.clear()
        progress_bar.visible = True
        progress_bar.value = 0
        status_text.visible = True
        status_text.value = "Iniciando varredura..."
        metrics_row.visible = True
        leads_container.visible = True
        filters_section.visible = False
        download_button.visible = False
        page.update()

        max_r = min(int(max_results_field.value or "100"), 1000)
        min_s = int(min_score_slider.value)
        criteria = criteria_field.value

        def run_in_background():
            nonlocal is_running
            try:
                def progress_cb(current, total, lead_name):
                    progress_bar.value = current / total
                    status_text.value = f"Lendo perfil: {lead_name}"
                    metrics_row.controls[0].content.controls[1].value = str(current)
                    page.update()

                raw_leads = scrape_leads(niche, region, source, max_results=max_r, block_large_portals=block_portals.value, on_progress=progress_cb)

                if not raw_leads:
                    status_text.value = "Nenhum perfil encontrado com esses termos."
                    return

                if require_contact.value:
                    raw_leads = [l for l in raw_leads if l.get('_has_contact')]
                    metrics_row.controls[0].content.controls[1].value = str(len(raw_leads))

                status_text.value = f"Avaliando {len(raw_leads)} leads com VELLIX IA..."
                progress_bar.value = None
                page.update()

                campaign_id = save_campaign(page, {
                    "name": f"Campanha {niche}", "niche": niche, "region": region, "source": source,
                    "criteria": criteria, "min_score": min_s, "max_results": max_r
                })

                batch_size = 20
                discarded = 0

                for i in range(0, len(raw_leads), batch_size):
                    batch = raw_leads[i:i + batch_size]
                    evaluations = evaluate_leads_batch(batch, api_key, criteria)

                    for j, result in enumerate(evaluations):
                        lead_data = batch[j]
                        score = result.get("score", 0)

                        if score >= min_s:
                            lead_doc = {
                                "name": lead_data["Nome"], "link": lead_data["Link"], "description": lead_data["Descricao (Bio/Web)"],
                                "has_phone": lead_data["Tem Telefone?"] == "Sim", "has_email": lead_data["Tem E-mail?"] == "Sim",
                                "score": score, "reason": result.get("reason"), "tags": result.get("tags"),
                                "decision_maker": result.get("decision_maker"), "whatsapp_ready": result.get("whatsapp_ready")
                            }
                            add_lead_to_campaign(page, campaign_id, lead_doc)
                            approved_leads.append(lead_doc)

                            card = _build_lead_card(lead_doc, len(approved_leads)-1)
                            leads_list.controls.append(card)
                            metrics_row.controls[1].content.controls[1].value = str(len(approved_leads))
                        else:
                            discarded += 1
                            metrics_row.controls[2].content.controls[1].value = str(discarded)

                        page.update()

                update_campaign_stats(campaign_id, len(raw_leads), len(approved_leads), discarded)
                status_text.value = f"Concluido! {len(approved_leads)} aprovados."
                progress_bar.visible = False
                download_button.visible = len(approved_leads) > 0
                filters_section.visible = len(approved_leads) > 0
                apply_filters(None)

            except Exception as e:
                status_text.value = f"Erro: {e}"
                progress_bar.visible = False
            finally:
                is_running = False
                run_button.content.disabled = False
                page.update()

        threading.Thread(target=run_in_background, daemon=True).start()

    view_main = ft.Column(
        controls=[
            ft.Container(content=ft.Column([ft.Text("Nova Prospeccao", size=24, weight=ft.FontWeight.W_700), ft.Text("Configure varredura inteligente", size=13, color=TEXT_SECONDARY)]), padding=ft.Padding.only(bottom=20)),
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.LOCATION_SEARCHING, size=16, color=TEXT_SECONDARY), ft.Text("ALVO", size=11, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)]),
                ft.ResponsiveRow([ft.Column(col={"sm":12, "md":4}, controls=[niche_field]), ft.Column(col={"sm":12, "md":4}, controls=[region_field]), ft.Column(col={"sm":12, "md":4}, controls=[source_dropdown])])
            ]), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER_SUBTLE), border_radius=14, padding=20),
            ft.Container(height=12),
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.PSYCHOLOGY, size=16, color=TEXT_SECONDARY), ft.Text("INTELIGENCIA", size=11, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)]),
                criteria_field,
                ft.ResponsiveRow([
                    ft.Column(col={"sm":12, "md":4}, controls=[ft.Column([min_score_label, min_score_slider])]),
                    ft.Column(col={"sm":12, "md":4}, controls=[max_results_field]),
                    ft.Column(col={"sm":12, "md":4}, controls=[ft.Column([require_contact, block_portals])])
                ])
            ]), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER_SUBTLE), border_radius=14, padding=20),
            ft.Container(height=16),
            ft.Row([run_button, download_button], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
            ft.Container(height=12),
            progress_bar, status_text, ft.Container(height=8),
            metrics_row, ft.Container(height=8),
            filters_section, ft.Container(height=8),
            leads_container, ft.Container(height=80)
        ],
        scroll=ft.ScrollMode.AUTO, expand=True, spacing=0
    )

    view = ft.Container(content=view_main, padding=ft.Padding.symmetric(horizontal=24, vertical=20), expand=True)

    copilot_ui = build_copilot_view(page)
    drawer = ft.Container(content=copilot_ui, width=420, bgcolor=BG_CARD, border=ft.Border(left=ft.BorderSide(1, BORDER_SUBTLE)), right=-430, top=0, bottom=0, shadow=ft.BoxShadow(spread_radius=0, blur_radius=50, color="#88000000"), animate=ft.Animation(500, ft.AnimationCurve.DECELERATE))
    overlay = ft.Container(expand=True, bgcolor="#33000000", blur=ft.Blur(10, 10, ft.BlurTileMode.CLAMP), visible=False, opacity=0, on_click=lambda _: toggle_copilot(None), animate_opacity=300)

    def toggle_copilot(e):
        if drawer.right == -430:
            overlay.visible = True
            page.update()
            drawer.right = 0
            overlay.opacity = 1
        else:
            drawer.right = -430
            overlay.opacity = 0
            page.update()
            def hide_overlay():
                time.sleep(0.3)
                overlay.visible = False
                page.update()
            threading.Thread(target=hide_overlay, daemon=True).start()
        page.update()

    fab = ft.Container(content=ft.FloatingActionButton(content=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, size=18), ft.Text("VELLIX IA", weight=ft.FontWeight.W_700)], spacing=4), bgcolor=ACCENT, foreground_color=BG_PRIMARY, on_click=toggle_copilot, width=130), right=24, bottom=24)

    return ft.Stack(controls=[view, overlay, fab, drawer], expand=True)