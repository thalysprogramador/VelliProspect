import flet as ft
import threading
from ai_evaluator import copilot_chat, generate_followup_plan
from database import get_all_leads, get_setting

BG = "#000000"
BG_CARD = "#1C1C1E"
BORDER = "#38383A"
TX = "#F5F5F7"
TX2 = "#86868B"
TX3 = "#48484A"
ACC = "#FFFFFF"

def build_copilot_view(page: ft.Page):
    msgs = ft.ListView(expand=True, spacing=16, auto_scroll=True, padding=24)
    inp = ft.TextField(
        hint_text="Pergunte ao VELLIX IA...", expand=True,
        border_color=BORDER, focused_border_color=ACC,
        text_style=ft.TextStyle(color=TX, size=14), hint_style=ft.TextStyle(color=TX3),
        bgcolor=BG_CARD, border_radius=28, content_padding=ft.Padding.symmetric(horizontal=20, vertical=14),
    )
    typing = ft.Row([ft.ProgressRing(width=14, height=14, stroke_width=2, color=ACC), ft.Text("Pensando...", color=TX2, size=12)], visible=False)

    def user_msg(text):
        msgs.controls.append(ft.Row([ft.Container(content=ft.Text(text, color=BG, size=14, font_family="Inter"), bgcolor=ACC, border_radius=20, padding=ft.Padding.symmetric(horizontal=18, vertical=12), width=480)], alignment=ft.MainAxisAlignment.END))
        page.update()

    def bot_msg(text):
        msgs.controls.append(ft.Row([ft.Container(content=ft.Markdown(text, selectable=True, extension_set="gitHubWeb", code_theme="atom-one-dark"), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=20, padding=ft.Padding.symmetric(horizontal=18, vertical=14), width=520)], alignment=ft.MainAxisAlignment.START))
        page.update()

    def send(e):
        text = inp.value.strip()
        if not text: return
        user_msg(text)
        inp.value = ""
        typing.visible = True
        page.update()
        def run():
            key = get_setting("gemini_api_key", "")
            if not key:
                bot_msg("Configure sua **API Key** na aba Configuracoes.")
            else:
                try:
                    leads = get_all_leads()
                    bot_msg(copilot_chat(text, leads, key))
                except Exception as ex:
                    bot_msg(f"Erro: {ex}")
            typing.visible = False
            page.update()
        threading.Thread(target=run, daemon=True).start()

    inp.on_submit = send

    def chip_click(e):
        inp.value = e.control.data
        send(None)

    chips = ft.Row([
        ft.OutlinedButton("Melhores leads", data="Qual o melhor lead?", on_click=chip_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), side=ft.BorderSide(1, BORDER), color=TX2)),
        ft.OutlinedButton("Pitch WhatsApp", data="Crie um pitch de WhatsApp para os top 3 leads", on_click=chip_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), side=ft.BorderSide(1, BORDER), color=TX2)),
        ft.OutlinedButton("Estrategia", data="Dicas de abordagem fria B2B", on_click=chip_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), side=ft.BorderSide(1, BORDER), color=TX2)),
    ], scroll=ft.ScrollMode.AUTO, spacing=8)

    bot_msg("Ola! Sou o **VELLIX IA**, seu assistente de prospeccao.\nComo posso ajudar?")

    return ft.Container(content=ft.Column([
        ft.Container(content=ft.Row([ft.Icon(ft.Icons.SMART_TOY, color=ACC, size=22), ft.Text("VELLIX IA", size=22, weight=ft.FontWeight.W_700, color=TX)], spacing=10), padding=ft.Padding.only(left=24, top=24, right=24, bottom=12)),
        msgs,
        ft.Container(content=ft.Column([typing, chips, ft.Row([inp, ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=ACC, on_click=send)], spacing=8)], spacing=10), padding=20, border=ft.Border.only(top=ft.BorderSide(1, BORDER)))
    ], expand=True), expand=True, bgcolor=BG)
