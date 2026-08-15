import flet as ft
import pandas as pd
import io
import base64
from datetime import datetime
from persistence import get_campaigns, delete_campaign
from database import get_campaign, get_leads_by_campaign, update_lead_status

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

TAG_COLORS = {"Ticket Alto": "#30D158", "Sem Site": "#FF453A", "Boa Presenca Digital": "#0A84FF", "Baixa Presenca Digital": "#FFD60A", "Franquia / Rede": "#BF5AF2", "Novo no Mercado": "#FF375F", "Decisor Acessivel": "#64D2FF", "Alta Concorrencia": "#FF9F0A", "E-commerce": "#5E5CE6", "Servico Local": "#30D158", "B2B": "#0A84FF", "B2C": "#FF375F", "Alto Potencial Digital": "#30D158"}

def _fmt_date(d):
    if not d: return ""
    try: return datetime.fromisoformat(str(d).replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except: return str(d)[:10]

def _status_color(s):
    return {"running": YEL, "completed": GREEN, "failed": RED}.get(s, TX3)

def _status_label(s):
    return {"running": "Ativo", "completed": "Concluida", "failed": "Falhou"}.get(s, (s or "").capitalize())

def _tag(t):
    c = TAG_COLORS.get(t, TX3)
    return ft.Container(content=ft.Text(t, size=10, weight=ft.FontWeight.W_600, color=c), bgcolor=f"{c}18", padding=ft.Padding.symmetric(horizontal=8, vertical=3), border_radius=6)

def build_campaigns_view(page: ft.Page):
    panel = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)

    def render_list():
        panel.controls.clear()
        panel.controls.append(ft.Container(content=ft.Column([ft.Text("Campanhas", size=34, weight=ft.FontWeight.W_700, color=TX), ft.Text("Historico de prospeccoes e leads.", size=15, color=TX2)], spacing=4), padding=ft.Padding.only(bottom=24)))
        camps = get_campaigns(page)
        if not camps:
            panel.controls.append(ft.Container(content=ft.Column([ft.Icon(ft.Icons.FOLDER_OPEN, size=48, color=TX3), ft.Text("Nenhuma campanha ainda.", size=16, color=TX2), ft.Text("Faca uma prospeccao para comecar.", size=14, color=TX3)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12), expand=True, alignment=ft.Alignment.CENTER))
            page.update()
            return
        for c in camps:
            sc = _status_color(c.get("status", ""))
            card = ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text(c.get("name", "Campanha"), size=17, weight=ft.FontWeight.W_700, color=TX, expand=True), ft.Container(content=ft.Text(_status_label(c.get("status")), size=10, weight=ft.FontWeight.W_700, color=sc), bgcolor=f"{sc}18", padding=ft.Padding.symmetric(horizontal=10, vertical=4), border_radius=6)]),
                    ft.Text(f"{c.get('niche','')} | {c.get('region','')} | {c.get('source','')}", size=13, color=TX2),
                    ft.Divider(color=BORDER, height=1),
                    ft.Row([ft.Text(_fmt_date(c.get("created_at")), size=12, color=TX3), ft.Container(expand=True), ft.Text(f"{c.get('total_approved', 0)} leads", size=13, weight=ft.FontWeight.W_600, color=GREEN)]),
                ], spacing=10),
                bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=16, padding=20,
                on_click=lambda e, cid=c.get("id"): detail(cid),
                on_hover=lambda e: (setattr(e.control, "bgcolor", BG_HOVER if e.data == "true" else BG_CARD), e.control.update()),
            )
            panel.controls.append(ft.Container(content=card, padding=ft.Padding.only(bottom=12)))
        page.update()

    def detail(cid):
        c = get_campaign(cid)
        if not c: return
        leads = get_leads_by_campaign(cid)
        panel.controls.clear()
        panel.controls.append(ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, icon_color=TX2, on_click=lambda e: render_list()),
            ft.Text(c.get("name",""), size=24, weight=ft.FontWeight.W_700, color=TX, expand=True),
            ft.IconButton(ft.Icons.DOWNLOAD, icon_color=TX2, on_click=lambda e: export(leads), tooltip="Exportar"),
            ft.IconButton(ft.Icons.DELETE, icon_color=RED, on_click=lambda e: (delete_campaign(cid), render_list()), tooltip="Apagar"),
        ]))
        panel.controls.append(ft.Text(f"{len(leads)} leads aprovados", size=14, color=GREEN))
        panel.controls.append(ft.Divider(color=BORDER))
        for l in leads:
            sc = int(l.get("score", 0))
            scol = GREEN if sc >= 8 else (YEL if sc >= 5 else RED)
            tags_row = ft.Row([_tag(t) for t in l.get("tags", [])], wrap=True, spacing=4)
            lid = l.get("id")
            dd = ft.Dropdown(options=[ft.dropdown.Option("approved","Aprovado"),ft.dropdown.Option("contacted","Contatado"),ft.dropdown.Option("responded","Respondeu"),ft.dropdown.Option("converted","Convertido"),ft.dropdown.Option("lost","Perdido")], value=l.get("status","approved"), width=130, height=36, text_size=11, on_change=lambda e, lid=lid: update_lead_status(lid, e.control.value), bgcolor=BG, border_color=BORDER)
            panel.controls.append(ft.Container(content=ft.Column([
                ft.Row([ft.Container(content=ft.Text(str(sc), size=14, weight=ft.FontWeight.W_800, color=BG), bgcolor=scol, width=34, height=34, border_radius=17, alignment=ft.Alignment.CENTER), ft.Column([ft.Text(l.get("name","N/A"), size=15, weight=ft.FontWeight.W_700, color=TX), ft.Text(l.get("link",""), size=11, color=TX3, selectable=True)], spacing=2, expand=True), dd]),
                tags_row,
                ft.Text(l.get("reason",""), size=13, color=TX2, italic=True),
            ], spacing=10), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=12, padding=16, margin=ft.Margin.only(bottom=10)))
        page.update()

    def export(leads):
        if not leads: return
        try:
            df = pd.DataFrame(leads)
            for col in ["campaign_id", "id", "created_at"]:
                if col in df.columns: df = df.drop(columns=[col])
            buf = io.BytesIO()
            df.to_excel(buf, index=False)
            buf.seek(0)
            page.launch_url(f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(buf.read()).decode()}")
        except Exception as ex:
            print(f"[Export] {ex}")

    render_list()
    return ft.Container(content=panel, padding=ft.Padding.symmetric(horizontal=32, vertical=28), expand=True)
