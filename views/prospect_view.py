import flet as ft
import threading
import time
import traceback
from scraper import scrape_leads, get_available_sources
from ai_evaluator import evaluate_leads_batch
from database import update_campaign_stats, get_setting
from persistence import save_campaign, add_lead_to_campaign

BG = "#000000"
BG_CARD = "#1C1C1E"
BG_HOVER = "#2C2C2E"
BORDER = "#38383A"
TX = "#F5F5F7"
TX2 = "#86868B"
TX3 = "#48484A"
ACC = "#FFFFFF"
GREEN = "#30D158"
YEL = "#FFD60A"
RED = "#FF453A"

TAG_COLORS = {"Ticket Alto": "#30D158", "Ticket Baixo": "#5E5CE6", "Sem Site": "#FF453A", "Boa Presenca Digital": "#0A84FF", "Baixa Presenca Digital": "#FFD60A", "Franquia / Rede": "#BF5AF2", "Novo no Mercado": "#FF375F", "Decisor Acessivel": "#64D2FF", "Alta Concorrencia": "#FF9F0A", "Oportunidade Urgente": "#FFD60A", "E-commerce": "#5E5CE6", "Servico Local": "#30D158", "B2B": "#0A84FF", "B2C": "#FF375F", "Alto Potencial Digital": "#30D158", "Tem Redes Sociais": "#0A84FF"}

def _tag(t):
    c = TAG_COLORS.get(t, TX3)
    return ft.Container(content=ft.Text(t, size=10, weight=ft.FontWeight.W_600, color=c), bgcolor=f"{c}18", padding=ft.Padding.symmetric(horizontal=8, vertical=3), border_radius=6)

def _metric(icon, label, value_ctrl, color):
    return ft.Container(content=ft.Column([ft.Row([ft.Icon(icon, size=16, color=color), ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=TX2)], spacing=6), value_ctrl], spacing=6), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=14, padding=18, expand=True)

def _lead_card(lead):
    sc = int(lead.get("score", 0))
    scol = GREEN if sc >= 8 else (YEL if sc >= 5 else RED)
    tags = ft.Row([_tag(t) for t in lead.get("tags", [])], wrap=True, spacing=4)
    return ft.Container(content=ft.Column([
        ft.Row([ft.Container(content=ft.Text(str(sc), size=14, weight=ft.FontWeight.W_800, color=BG), bgcolor=scol, width=34, height=34, border_radius=17, alignment=ft.Alignment.CENTER), ft.Column([ft.Text(lead.get("name", "N/A"), size=16, weight=ft.FontWeight.W_700, color=TX), ft.Text(lead.get("link", ""), size=11, color=TX3, selectable=True)], spacing=2, expand=True)]),
        tags,
        ft.Text(f"\"{lead.get('reason', '')}\"", size=13, color=TX2, italic=True),
    ], spacing=10), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=14, padding=18, margin=ft.Margin.only(bottom=10))

def build_prospect_view(page: ft.Page):
    niche = ft.TextField(label="Nicho (ex: Dentistas)", expand=True, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD)
    region = ft.TextField(label="Regiao (ex: Sao Paulo)", expand=True, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD)

    try: sources = get_available_sources()
    except: sources = ["Todas as Fontes"]

    source_dd = ft.Dropdown(label="Canal", options=[ft.dropdown.Option(s) for s in sources], value=sources[0], expand=True, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD)
    criteria = ft.TextField(label="Criterios de Qualificacao (IA)", multiline=True, min_lines=2, max_lines=3, value="Busque negocios premium com potencial de investir em marketing digital.", border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD)
    max_res = ft.TextField(label="Max", value="50", width=100, border_color=BORDER, focused_border_color=ACC, text_style=ft.TextStyle(size=14, color=TX), bgcolor=BG_CARD)
    min_score = ft.Slider(min=1, max=10, divisions=9, value=5, label="Min: {value}")
    req_contact = ft.Checkbox(label="Exigir contato", value=False, check_color=BG, active_color=ACC)
    block_portals = ft.Checkbox(label="Ignorar portais", value=True, check_color=BG, active_color=ACC)

    progress = ft.ProgressBar(color=ACC, bgcolor=BORDER, value=0, visible=False)
    status = ft.Text("", size=13, color=TX2, text_align=ft.TextAlign.CENTER)

    txt_lidos = ft.Text("0", size=28, weight=ft.FontWeight.W_800, color=TX)
    txt_aprov = ft.Text("0", size=28, weight=ft.FontWeight.W_800, color=GREEN)
    txt_desc = ft.Text("0", size=28, weight=ft.FontWeight.W_800, color=RED)
    metrics = ft.Row([_metric(ft.Icons.SEARCH, "Lidos", txt_lidos, ACC), _metric(ft.Icons.CHECK_CIRCLE, "Aprovados", txt_aprov, GREEN), _metric(ft.Icons.CANCEL, "Descartados", txt_desc, RED)], spacing=12, visible=False)

    leads_list = ft.ListView(expand=True, spacing=0)
    current_data = []

    btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.ROCKET_LAUNCH, size=18, color=BG), ft.Text("INICIAR PROSPECCAO", size=15, weight=ft.FontWeight.W_700, color=BG)], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ACC, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14), padding=ft.Padding.symmetric(vertical=20, horizontal=40), elevation=0),
    )

    def start(e):
        n = niche.value.strip() if niche.value else ""
        r = region.value.strip() if region.value else ""
        if not n or not r:
            status.value = "Preencha Nicho e Regiao."
            status.color = RED
            page.update()
            return
        api_key = get_setting("gemini_api_key", "")
        if not api_key:
            status.value = "Configure sua API Key em Configuracoes."
            status.color = RED
            page.update()
            return

        btn.disabled = True
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
                    btn.disabled = False
                    page.update()
                    return

                txt_lidos.value = str(len(scraped))
                page.update()

                filtered = [s for s in scraped if not req_contact.value or s.get("_has_contact")]
                disc_contact = len(scraped) - len(filtered)
                txt_desc.value = str(disc_contact)

                if not filtered:
                    status.value = "Todos filtrados (sem contato)."
                    status.color = YEL
                    update_campaign_stats(cid, len(scraped), 0, len(scraped), "completed")
                    progress.visible = False
                    btn.disabled = False
                    page.update()
                    return

                approved = 0
                disc_ai = 0
                batch = 10
                for i in range(0, len(filtered), batch):
                    b = filtered[i:i+batch]
                    status.value = f"IA avaliando lote {i//batch+1}..."
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
                            leads_list.controls.append(_lead_card(ld))
                            approved += 1
                        else:
                            disc_ai += 1
                    txt_aprov.value = str(approved)
                    txt_desc.value = str(disc_contact + disc_ai)
                    page.update()
                    if i + batch < len(filtered): time.sleep(1)

                status.value = f"Concluido! {approved} leads aprovados."
                status.color = GREEN
                progress.value = 1.0
                update_campaign_stats(cid, len(scraped), approved, disc_contact + disc_ai, "completed")
            except Exception as ex:
                traceback.print_exc()
                status.value = f"Erro: {ex}"
                status.color = RED
            progress.visible = False
            btn.disabled = False
            page.update()

        threading.Thread(target=run, daemon=True).start()

    btn.on_click = start

    return ft.Container(content=ft.Column([
        ft.Container(content=ft.Column([
            ft.Image(src="logo_velli.png", width=160, height=50),
            ft.Container(height=16),
            ft.Text("Nova Prospeccao", size=34, weight=ft.FontWeight.W_700, color=TX),
            ft.Text("Encontre leads qualificados com inteligencia artificial.", size=15, color=TX2),
        ], spacing=4), padding=ft.Padding.only(bottom=28)),
        ft.Container(content=ft.Column([
            ft.Row([niche, region], spacing=12),
            ft.Row([source_dd, max_res], spacing=12),
            ft.Row([req_contact, block_portals], spacing=12),
            criteria,
            ft.Row([ft.Text("Nota minima:", size=13, color=TX2), ft.Container(content=min_score, expand=True)], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=4),
            btn,
        ], spacing=14), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=18, padding=28),
        ft.Container(height=16),
        ft.Column([progress, status], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Container(height=12),
        metrics,
        ft.Container(height=20),
        ft.Text("Leads Aprovados", size=20, weight=ft.FontWeight.W_700, color=TX),
        ft.Container(height=8),
        leads_list,
    ], scroll=ft.ScrollMode.AUTO, expand=True), padding=ft.Padding.symmetric(horizontal=32, vertical=28), expand=True)
