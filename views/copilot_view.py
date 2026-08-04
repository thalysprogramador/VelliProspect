import flet as ft
import threading
from ai_evaluator import copilot_chat, generate_followup_plan
from database import get_all_leads, get_setting

BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BORDER_SUBTLE = "#2A2A2A"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"

def build_copilot_view(page: ft.Page):
    messages_list = ft.ListView(expand=True, spacing=15, auto_scroll=True, padding=20)
    input_field = ft.TextField(
        hint_text="Pergunte ao VELLIX IA...",
        expand=True,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        text_style=ft.TextStyle(color=TEXT_PRIMARY, font_family="Inter", size=14),
        hint_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        bgcolor=BG_CARD,
        border_radius=20,
        content_padding=15
    )

    thinking_indicator = ft.Row(
        [
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ACCENT),
            ft.Text("VELLIX IA esta digitando...", color=TEXT_SECONDARY, size=12, font_family="Inter")
        ],
        visible=False,
        alignment=ft.MainAxisAlignment.START
    )

    def add_user_message(text):
        messages_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, color=BG_PRIMARY, font_family="Inter", size=14),
                        bgcolor=ACCENT,
                        border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_left=15),
                        padding=15,
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def add_copilot_message(text):
        messages_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Markdown(text, selectable=True, extension_set="gitHubWeb", 
                                            code_theme="atom-one-dark"),
                        bgcolor=BG_CARD,
                        border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_right=15),
                        padding=15,
                        width=min(int(page.width * 0.7) if page.width else 600, 600),
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        page.update()

    def send_message(e):
        text = input_field.value.strip()
        if not text: return

        add_user_message(text)
        input_field.value = ""
        thinking_indicator.visible = True
        page.update()

        def do_chat():
            api_key = get_setting("gemini_api_key", "")
            if not api_key:
                add_copilot_message("Voce precisa configurar a API Key na aba Configuracoes primeiro.")
                thinking_indicator.visible = False
                page.update()
                return

            try:
                leads = get_all_leads()
                response = copilot_chat(text, leads, api_key)
                add_copilot_message(response)
            except Exception as ex:
                add_copilot_message(f"Ocorreu um erro: {ex}")
            
            thinking_indicator.visible = False
            page.update()

        threading.Thread(target=do_chat, daemon=True).start()

    input_field.on_submit = send_message
    send_btn = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=ACCENT, on_click=send_message)

    # Mensagem de Boas-vindas
    add_copilot_message(
        "Ola! Eu sou o **VELLIX IA**, seu assistente de prospeccao.\n"
        "Tenho acesso aos seus leads. Como posso ajudar hoje?"
    )

    def suggestion_click(e):
        input_field.value = e.control.data
        send_message(None)

    suggestions = ft.Row(
        controls=[
            ft.ElevatedButton("Melhores leads", data="Qual o melhor lead?", on_click=suggestion_click,
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), bgcolor=BG_CARD, color=TEXT_PRIMARY)),
            ft.ElevatedButton("Pitch WhatsApp", data="Crie um pitch para WhatsApp para os top 3 leads", on_click=suggestion_click,
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), bgcolor=BG_CARD, color=TEXT_PRIMARY)),
            ft.ElevatedButton("Dicas frias", data="Dicas de abordagem fria B2B", on_click=suggestion_click,
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), bgcolor=BG_CARD, color=TEXT_PRIMARY))
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY, color=ACCENT, size=24),
                        ft.Text("VELLIX IA Copilot", size=20, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter")
                    ]),
                    padding=ft.Padding.only(left=20, top=20, right=20)
                ),
                messages_list,
                ft.Container(
                    content=ft.Column([
                        thinking_indicator,
                        suggestions,
                        ft.Row([input_field, send_btn])
                    ]),
                    padding=20,
                    bgcolor=BG_PRIMARY,
                    border=ft.border.only(top=ft.BorderSide(1, BORDER_SUBTLE))
                )
            ],
            expand=True
        ),
        expand=True,
        bgcolor=BG_PRIMARY
    )