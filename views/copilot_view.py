import flet as ft
import threading
from ai_evaluator import copilot_chat, generate_followup_plan
from database import get_all_leads, get_setting

BG = "#000000"
BG_CARD = "#141415"
BG_HOVER = "#242426"
BORDER = "#2C2C2E"
TX = "#FFFFFF"
TX2 = "#A1A1A6"
TX3 = "#6E6E73"
ACC = "#2997FF"

def build_copilot_view(page: ft.Page):
    msgs = ft.ListView(expand=True, spacing=24, auto_scroll=True, padding=32)
    inp = ft.TextField(
        hint_text="Pergunte ao VELLIX IA...", expand=True,
        border_color=BORDER, focused_border_color=ACC,
        text_style=ft.TextStyle(color=TX, size=15), hint_style=ft.TextStyle(color=TX3),
        bgcolor=BG_CARD, border_radius=24, content_padding=ft.Padding.symmetric(horizontal=24, vertical=16),
    )
    typing = ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2, color=ACC), ft.Text("Analisando dados...", color=TX2, size=13)], visible=False)

    def user_msg(text):
        msgs.controls.append(ft.Row([ft.Container(content=ft.Text(text, color=BG, size=15, font_family="Inter", weight=ft.FontWeight.W_500), bgcolor=ACC, border_radius=20, padding=ft.Padding.symmetric(horizontal=20, vertical=14), width=480, shadow=ft.BoxShadow(spread_radius=0, blur_radius=20, color=f"{ACC}30", offset=ft.Offset(0, 4)))], alignment=ft.MainAxisAlignment.END))
        page.update()

    def bot_msg(text):
        msgs.controls.append(ft.Row([ft.Container(content=ft.Markdown(text, selectable=True, extension_set="gitHubWeb", code_theme="atom-one-dark"), bgcolor=BG_CARD, border=ft.Border.all(1, BORDER), border_radius=20, padding=ft.Padding.symmetric(horizontal=20, vertical=16), width=600, shadow=ft.BoxShadow(spread_radius=0, blur_radius=20, color=f"{BG}40", offset=ft.Offset(0, 4)))], alignment=ft.MainAxisAlignment.START))
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
        ft.OutlinedButton("Melhores leads", data="Quais sao os top 3 melhores leads para abordar agora e por que?", on_click=chip_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), side=ft.BorderSide(1, BORDER), color=TX2, bgcolor=BG_CARD)),
        ft.OutlinedButton("Pitch WhatsApp", data="Crie um pitch de WhatsApp para quebrar o gelo com o melhor lead", on_click=chip_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), side=ft.BorderSide(1, BORDER), color=TX2, bgcolor=BG_CARD)),
        ft.OutlinedButton("Estrategia", data="Quais padroes os nossos piores leads (notas 1 a 4) tem em comum?", on_click=chip_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), side=ft.BorderSide(1, BORDER), color=TX2, bgcolor=BG_CARD)),
    ], scroll=ft.ScrollMode.AUTO, spacing=12)

    bot_msg("Ola! Eu sou o **VELLIX IA**, a inteligencia artificial desenhada para potencializar suas vendas.\nTenho acesso total ao seu CRM e historico de leads. Como posso te ajudar a escalar hoje?")

    return ft.Container(content=ft.Column([
        ft.Container(content=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, color=ACC, size=28), ft.Text("VELLIX IA", size=28, weight=ft.FontWeight.W_600, color=TX)], spacing=12), padding=ft.Padding.only(left=32, top=32, right=32, bottom=16)),
        msgs,
        ft.Container(content=ft.Column([typing, chips, ft.Row([inp, ft.IconButton(icon=ft.Icons.ARROW_UPWARD_ROUNDED, icon_color=BG, bgcolor=ACC, on_click=send, width=48, height=48)], spacing=12)], spacing=12), padding=24, border=ft.Border.only(top=ft.BorderSide(1, BORDER)), bgcolor=BG_CARD)
    ], expand=True), expand=True, bgcolor=BG)
