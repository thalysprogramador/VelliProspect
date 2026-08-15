import flet as ft
import threading
import time
import traceback
from scraper import scrape_leads, get_available_sources
from ai_evaluator import evaluate_leads_batch
from database import update_campaign_stats, get_setting
from persistence import save_campaign, add_lead_to_campaign

# Apple Premium Design Tokens
BG = "#000000"
BG_CARD = "#141415"
BG_HOVER = "#242426"
BORDER = "#2C2C2E"
TX = "#FFFFFF"
TX2 = "#A1A1A6"
TX3 = "#6E6E73"
ACC = "#2997FF" # Apple Blue
GREEN = "#30D158"
YEL = "#FFD60A"
RED = "#FF453A"

TAG_COLORS = {"Ticket Alto": "#30D158", "Ticket Baixo": "#5E5CE6", "Sem Site": "#FF453A", "Boa Presenca Digital": "#2997FF", "Baixa Presenca Digital": "#FFD60A", "Franquia / Rede": "#BF5AF2", "Novo no Mercado": "#FF375F", "Decisor Acessivel": "#64D2FF", "Alta Concorrencia": "#FF9F0A", "Oportunidade Urgente": "#FFD60A", "E-commerce": "#5E5CE6", "Servico Local": "#30D158", "B2B": "#2997FF", "B2C": "#FF375F", "Alto Potencial Digital": "#30D158", "Tem Redes Sociais": "#2997FF"}

def _tag(t):
    c = TAG_COLORS.get(t, TX3)
    return ft.Container(content=ft.Text(t, size=11, weight=ft.FontWeight.W_600, color=c), bgcolor=f"{c}15", padding=ft.Padding.symmetric(horizontal=10, vertical=4), border_radius=8)

def _metric(icon, label, value_ctrl, color):
    return ft.Container(content=ft.Column([ft.Row([ft.Icon(icon, size=18, color=color), ft.Text(label, size=13, weight=ft.FontWeight.W_500, color=TX2)], spacing=6), value_ctrl], spacing=8), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=16, padding=20, expand=True)

def _lead_card(lead, page):
    sc = int(lead.get("score", 0))
    scol = GREEN if sc >= 8 else (YEL if sc >= 5 else RED)
    tags = ft.Row([_tag(t) for t in lead.get("tags", [])], wrap=True, spacing=6)
    
    link = lead.get("link", "")
    btn_visit = ft.ElevatedButton(
        text="Acessar Fonte",
        icon=ft.Icons.OPEN_IN_NEW,
        bgcolor=ACC,
        color=TX,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=0, padding=12),
        on_click=lambda e: page.launch_url(link) if link else None,
        visible=bool(link)
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Container(content=ft.Text(str(sc), size=16, weight=ft.FontWeight.W_700, color=BG), bgcolor=scol, width=38, height=38, border_radius=19, alignment=ft.Alignment.CENTER),
                ft.Column([ft.Text(lead.get("name", "N/A"), size=17, weight=ft.FontWeight.W_600, color=TX), ft.Text(link, size=12, color=TX3, selectable=True)], spacing=2, expand=True),
                btn_visit
            ]),
            ft.Container(height=4),
            tags,
            ft.Container(height=4),
            ft.Text(f"\"{lead.get('reason', '')}\"", size=14, color=TX2, italic=True),
        ], spacing=8),
        bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=16, padding=24, margin=ft.Margin.only(bottom=16),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=20, color=f"{BG}40", offset=ft.Offset(0, 4))
    )

def build_prospect_view(page: ft.Page):
    niche = ft.TextField(label="Nicho de Mercado (ex: Odontologia)", expand=True, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD, border_radius=12)
    region = ft.TextField(label="Regiao / Cidade (ex: Sao Paulo, SP)", expand=True, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD, border_radius=12)

    try: sources = get_available_sources()
    except: sources = ["Todas as Fontes"]

    source_dd = ft.Dropdown(label="Canal de Busca", options=[ft.dropdown.Option(s) for s in sources], value=sources[0], expand=True, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD, border_radius=12)
    criteria = ft.TextField(label="Criterios de Qualificacao da Inteligencia Artificial", multiline=True, min_lines=2, max_lines=3, value="Busque negocios premium com potencial de investir em marketing digital.", border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD, border_radius=12)
    max_res = ft.TextField(label="Max", value="50", width=100, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD, border_radius=12)
    min_score = ft.Slider(min=1, max=10, divisions=9, value=5, label="Nota Minima: {value}", active_color=ACC)
    req_contact = ft.Checkbox(label="Exigir contato visivel", value=False, check_color=BG, active_color=ACC)
    block_portals = ft.Checkbox(label="Ignorar portais (Ifood, etc)", value=True, check_color=BG, active_color=ACC)

    progress = ft.ProgressBar(color=ACC, bgcolor=BORDER, value=0, visible=False)
    status = ft.Text("", size=14, color=TX2, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_500)

    txt_lidos = ft.Text("0", size=32, weight=ft.FontWeight.W_700, color=TX)
    txt_aprov = ft.Text("0", size=32, weight=ft.FontWeight.W_700, color=GREEN)
    txt_desc = ft.Text("0", size=32, weight=ft.FontWeight.W_700, color=RED)
    metrics = ft.Row([_metric(ft.Icons.SEARCH, "Lidos", txt_lidos, ACC), _metric(ft.Icons.CHECK_CIRCLE, "Aprovados", txt_aprov, GREEN), _metric(ft.Icons.CANCEL, "Descartados", txt_desc, RED)], spacing=16, visible=False)

    leads_list = ft.ListView(expand=True, spacing=0)
    current_data = []

    btn_content = ft.Row([ft.Icon(ft.Icons.ROCKET_LAUNCH, size=20, color=BG), ft.Text("INICIAR PROSPECCAO", size=15, weight=ft.FontWeight.W_700, color=BG)], spacing=12, alignment=ft.MainAxisAlignment.CENTER)
    
    # Wrap button in a container to manage opacity smoothly
    btn_wrapper = ft.Container(
        content=ft.ElevatedButton(
            content=btn_content,
            bgcolor=ACC,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), padding=ft.Padding.symmetric(vertical=24, horizontal=40), elevation=0),
            on_click=lambda e: start(e)
        ),
        animate_opacity=300,
        opacity=1.0
    )

    def start(e):
        n = niche.value.strip() if niche.value else ""
        r = region.value.strip() if region.value else ""
        if not n or not r:
            status.value = "Por favor, preencha o Nicho e a Regiao."
            status.color = RED
            page.update()
            return
        api_key = get_setting("gemini_api_key", "")
        if not api_key:
            status.value = "Configure sua API Key em Configuracoes."
            status.color = RED
            page.update()
            return

        # UI State: Disabled and Low Opacity
        btn_wrapper.content.disabled = True
        btn_wrapper.opacity = 0.5
        progress.visible = True
        progress.value = 0
        metrics.visible = True
        leads_list.controls.clear()
        current_data.clear()
        txt_lidos.value = "0"
        txt_aprov.value = "0"
        txt_desc.value = "0"
        status.color = TX2
        page.update()

        def run():
            try:
                status.value = f"Varrendo: {n} em {r}..."
                page.update()
                cid = save_campaign(page, {"name": f"{n} em {r}", "niche": n, "region": r, "source": source_dd.value, "criteria": criteria.value, "min_score": int(min_score.value), "max_results": int(max_res.value or "50")})

                def prog(cur, tot, name):
                    status.value = f"Extraindo ({cur}/{tot}): {name[:35]}..."
                    progress.value = (cur / max(tot, 1)) * 0.3
                    page.update()

                scraped = scrape_leads(n, r, source_dd.value, int(max_res.value or "50"), block_portals.value, prog)
                if not scraped:
                    status.value = "Nenhum resultado. Tente outros termos."
                    status.color = YEL
                    update_campaign_stats(cid, 0, 0, 0, "failed")
                    progress.visible = False
                    btn_wrapper.content.disabled = False
                    btn_wrapper.opacity = 1.0
                    page.update()
                    return

                txt_lidos.value = str(len(scraped))
                page.update()

                filtered = [s for s in scraped if not req_contact.value or s.get("_has_contact")]
                disc_contact = len(scraped) - len(filtered)
                txt_desc.value = str(disc_contact)

                if not filtered:
                    status.value = "Todos os leads foram filtrados (sem contato)."
                    status.color = YEL
                    update_campaign_stats(cid, len(scraped), 0, len(scraped), "completed")
                    progress.visible = False
                    btn_wrapper.content.disabled = False
                    btn_wrapper.opacity = 1.0
                    page.update()
                    return

                approved = 0
                disc_ai = 0
                batch = 10
                for i in range(0, len(filtered), batch):
                    b = filtered[i:i+batch]
                    status.value = f"IA analisando lote {i//batch+1}..."
                    progress.value = 0.3 + (i/max(len(filtered),1)) * 0.7
                    page.update()

                    results = evaluate_leads_batch(b, api_key, criteria.value)
                    for j, res in enumerate(results):
                        lead = b[j]
                        sc = res.get("score", 0)
                        if sc >= int(min_score.value):
                            ld = {"name": lead.get("Nome",""), "link": lead.get("Link",""), "description": lead.get("Descricao (Bio/Web)",""), "has_phone": lead.get("Tem Telefone?")=="Sim", "has_email": lead.get("Tem E-mail?")=="Sim", "score": sc, "reason": res.get("reason",""), "tags": res.get("tags",[]), "decision_maker": res.get("decision_maker",""), "whatsapp_ready": res.get("whatsapp_ready", False)}
                            add_lead_to_campaign(page, cid, ld)
                            current_data.append(ld)
                            leads_list.controls.append(_lead_card(ld, page))
                            approved += 1
                        else:
                            disc_ai += 1
                    txt_aprov.value = str(approved)
                    txt_desc.value = str(disc_contact + disc_ai)
                    page.update()
                    if i + batch < len(filtered): time.sleep(1)

                status.value = f"Concluido! {approved} leads aprovados de alta qualidade."
                status.color = GREEN
                progress.value = 1.0
                update_campaign_stats(cid, len(scraped), approved, disc_contact + disc_ai, "completed")
            except Exception as ex:
                traceback.print_exc()
                status.value = f"Erro no processo: {ex}"
                status.color = RED
            progress.visible = False
            # Restore UI State
            btn_wrapper.content.disabled = False
            btn_wrapper.opacity = 1.0
            page.update()

        threading.Thread(target=run, daemon=True).start()

    return ft.Container(content=ft.Column([
        ft.Container(content=ft.Row([
            ft.Image(src="logo_velli_white.png", width=200, height=60),
            ft.Container(width=1, height=40, bgcolor=BORDER, margin=ft.Margin.symmetric(horizontal=16)),
            ft.Text("Transformando negocios comuns em marcas extraordinarias.", size=12, color=TX3, italic=True, weight=ft.FontWeight.W_500, expand=True)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=ft.Padding.only(bottom=24)),
        ft.Container(content=ft.Column([
            ft.Text("Motor de Prospeccao", size=28, weight=ft.FontWeight.W_600, color=TX, font_family="Inter"),
            ft.Text("Inteligencia artificial aplicada a vendas B2B.", size=15, color=TX2),
            ft.Container(height=12),
            ft.Row([niche, region], spacing=16),
            ft.Row([source_dd, max_res], spacing=16),
            ft.Row([req_contact, block_portals], spacing=16),
            criteria,
            ft.Row([ft.Text("Filtro de Nota Minima:", size=14, weight=ft.FontWeight.W_500, color=TX2), ft.Container(content=min_score, expand=True)], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=8),
            btn_wrapper,
        ], spacing=16), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=20, padding=32),
        ft.Container(height=24),
        ft.Column([progress, status], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Container(height=16),
        metrics,
        ft.Container(height=32),
        ft.Text("Leads Selecionados", size=24, weight=ft.FontWeight.W_600, color=TX),
        ft.Container(height=12),
        leads_list,
    ], scroll=ft.ScrollMode.AUTO, expand=True), padding=ft.Padding.symmetric(horizontal=40, vertical=32), expand=True)
