import flet as ft
import pandas as pd
import io
import base64
from datetime import datetime
from persistence import get_campaigns, delete_campaign
from database import get_campaign, get_leads_by_campaign, update_lead_status

BG = "#000000"
BG_CARD = "#141415"
BG_HOVER = "#242426"
BORDER = "#2C2C2E"
TX = "#FFFFFF"
TX2 = "#A1A1A6"
TX3 = "#6E6E73"
ACC = "#2997FF"
GREEN = "#30D158"
YEL = "#FFD60A"
RED = "#FF453A"

TAG_COLORS = {"Ticket Alto": "#30D158", "Ticket Baixo": "#5E5CE6", "Sem Site": "#FF453A", "Boa Presenca Digital": "#2997FF", "Baixa Presenca Digital": "#FFD60A", "Franquia / Rede": "#BF5AF2", "Novo no Mercado": "#FF375F", "Decisor Acessivel": "#64D2FF", "Alta Concorrencia": "#FF9F0A", "Oportunidade Urgente": "#FFD60A", "E-commerce": "#5E5CE6", "Servico Local": "#30D158", "B2B": "#2997FF", "B2C": "#FF375F", "Alto Potencial Digital": "#30D158", "Tem Redes Sociais": "#2997FF"}

def _fmt_date(d):
    if not d: return ""
    try: return datetime.fromisoformat(str(d).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except: return str(d)[:16]

def _status_color(s):
    return {"running": YEL, "completed": GREEN, "failed": RED}.get(s, TX3)

def _status_label(s):
    return {"running": "Em Andamento", "completed": "Concluida", "failed": "Falhou"}.get(s, (s or "").capitalize())

def _tag(t):
    c = TAG_COLORS.get(t, TX3)
    return ft.Container(content=ft.Text(t, size=11, weight=ft.FontWeight.W_600, color=c), bgcolor=f"{c}15", padding=ft.Padding.symmetric(horizontal=10, vertical=4), border_radius=8)

def build_campaigns_view(page: ft.Page):
    panel = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)

    def render_list():
        panel.controls.clear()
        panel.controls.append(ft.Container(content=ft.Column([
            ft.Text("Historico de Campanhas", size=28, weight=ft.FontWeight.W_600,  font_family="Inter"),
            ft.Text("Gerencie e exporte seus leads estruturados.", size=15, color=TX2)
        ], spacing=4), padding=ft.Padding.only(bottom=32)))
        
        camps = get_campaigns(page)
        if not camps:
            panel.controls.append(ft.Container(content=ft.Column([ft.Icon(ft.Icons.DATA_ARRAY, size=56, color=TX3), ft.Text("Nenhuma campanha.", size=18, weight=ft.FontWeight.W_500, color=TX2), ft.Text("Sua base de dados esta limpa.", size=14, color=TX3)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12), expand=True, alignment=ft.Alignment.CENTER))
            page.update()
            return
            
        for c in camps:
            sc = _status_color(c.get("status", ""))
            card = ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text(c.get("name", "Campanha"), size=18, weight=ft.FontWeight.W_600,  expand=True), ft.Container(content=ft.Text(_status_label(c.get("status")), size=11, weight=ft.FontWeight.W_700, color=sc), bgcolor=f"{sc}15", padding=ft.Padding.symmetric(horizontal=12, vertical=6), border_radius=8)]),
                    ft.Text(f"{c.get('niche','')}  ·  {c.get('region','')}  ·  {c.get('source','')}", size=14, color=TX2, weight=ft.FontWeight.W_500),
                    ft.Divider(color=BORDER, height=20),
                    ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=TX3), ft.Text(_fmt_date(c.get("created_at")), size=13, color=TX3), 
                        ft.Container(expand=True), 
                        ft.Text(f"{c.get('total_approved', 0)} leads qualificados", size=14, weight=ft.FontWeight.W_600, color=GREEN)
                    ]),
                ], spacing=6),
                bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=16, padding=24,
                on_click=lambda e, cid=c.get("id"): detail(cid),
                on_hover=lambda e: (setattr(e.control, "bgcolor", BG_HOVER if e.data == "true" else BG_CARD), e.control.update()),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=20, color=f"{BG}40", offset=ft.Offset(0, 4))
            )
            panel.controls.append(ft.Container(content=card, padding=ft.Padding.only(bottom=16)))
        page.update()

    def detail(cid):
        c = get_campaign(cid)
        if not c: return
        leads = get_leads_by_campaign(cid)
        panel.controls.clear()
        
        btn_export = ft.ElevatedButton(
            content=ft.Row([ft.Icon(ft.Icons.DOWNLOAD_ROUNDED,  size=16), ft.Text("Exportar Planilha (XLSX)",  size=13, weight=ft.FontWeight.W_600)], spacing=6),
            bgcolor=ACC, 
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=0),
            on_click=lambda e: export(leads, c.get("name"))
        )
        
        panel.controls.append(ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color=TX, on_click=lambda e: render_list(), style=ft.ButtonStyle(bgcolor=BG_CARD)),
            ft.Text(c.get("name",""), size=24, weight=ft.FontWeight.W_600,  expand=True),
            btn_export,
            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED, tooltip="Apagar Campanha", on_click=lambda e: (delete_campaign(cid), render_list()), style=ft.ButtonStyle(bgcolor=BG_CARD)),
        ], spacing=16))
        
        panel.controls.append(ft.Container(height=16))
        panel.controls.append(ft.Text(f"{len(leads)} leads extraidos e aprovados pela IA", size=15, color=GREEN, weight=ft.FontWeight.W_500))
        panel.controls.append(ft.Divider(color=BORDER, height=32))
        
        for l in leads:
            sc = int(l.get("score", 0))
            scol = GREEN if sc >= 8 else (YEL if sc >= 5 else RED)
            tags_row = ft.Row([_tag(t) for t in l.get("tags", [])], wrap=True, spacing=6),
            lid = l.get("id")
            
            link = l.get("link", "")
            btn_visit = ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, icon_color=ACC, tooltip="Acessar Fonte", on_click=lambda e, lnk=link: page.launch_url(lnk) if lnk else None, visible=bool(link))
            
            dd = ft.Dropdown(options=[ft.dropdown.Option("approved","Aprovado"),ft.dropdown.Option("contacted","Contatado"),ft.dropdown.Option("responded","Respondeu"),ft.dropdown.Option("converted","Convertido"),ft.dropdown.Option("lost","Perdido")], value=l.get("status","approved"), width=140, height=40, text_size=13, on_change=lambda e, lid=lid: update_lead_status(lid, e.control.value), bgcolor=BG, border_color=BORDER, border_radius=8)
            
            panel.controls.append(ft.Container(content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(str(sc), size=16, weight=ft.FontWeight.W_700, color=BG), bgcolor=scol, width=38, height=38, border_radius=19, alignment=ft.Alignment.CENTER), 
                    ft.Column([ft.Text(l.get("name","N/A"), size=17, weight=ft.FontWeight.W_600, color=TX), ft.Text(link, size=12, color=TX3, selectable=True)], spacing=2, expand=True), 
                    btn_visit,
                    dd
                ]),
                ft.Container(height=4),
                tags_row,
                ft.Container(height=4),
                ft.Text(f"\"{l.get('reason','')}\"", size=14, color=TX2, italic=True),
            ], spacing=8), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=16, padding=24, margin=ft.Margin.only(bottom=16), shadow=ft.BoxShadow(spread_radius=0, blur_radius=20, color=f"{BG}40", offset=ft.Offset(0, 4))))
        page.update()

    def export(leads, camp_name):
        if not leads: return
        try:
            # Format data to be highly professional
            formatted_leads = []
            for l in leads:
                formatted_leads.append({
                    "Nome da Empresa": l.get("name", ""),
                    "Nota (1 a 10)": l.get("score", ""),
                    "Status": l.get("status", ""),
                    "Telefone?": "Sim" if l.get("has_phone") else "Nao",
                    "Email?": "Sim" if l.get("has_email") else "Nao",
                    "Quem Atende": l.get("decision_maker", ""),
                    "Tags de Perfil": ", ".join(l.get("tags", [])),
                    "Analise da IA": l.get("reason", ""),
                    "Link de Contato": l.get("link", ""),
                    "Data de Captura": _fmt_date(l.get("created_at")),
                    "Bio Original": l.get("description", "")
                })
            
            df = pd.DataFrame(formatted_leads)
            buf = io.BytesIO()
            df.to_excel(buf, index=False, sheet_name=str(camp_name)[:31])
            buf.seek(0)
            
            # Send file directly
            page.launch_url(f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(buf.read()).decode()}")
        except Exception as ex:
            print(f"[Export] {ex}")

    render_list()
    return ft.Container(content=panel, padding=ft.Padding.symmetric(horizontal=40, vertical=32), expand=True)

