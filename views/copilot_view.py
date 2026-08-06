import flet as ft
import threading
from ai_evaluator import copilot_chat, generate_followup_plan
from database import get_all_leads, get_setting

BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BG_SURFACE = "#0F0F0F"
BG_ELEVATED = "#1A1A1A"
BORDER_SUBTLE = "#1F1F1F"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#8A8A8A"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
SUCCESS = "#34D399"
ERROR = "#F87171"

def build_copilot_view(page: ft.Page):
    messages_list = ft.ListView(expand=True, spacing=12, auto_scroll=True, padding=20)
    input_field = ft.TextField(
        hint_text="Pergunte ao VELLIX IA...",
        expand=True,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        text_style=ft.TextStyle(color=TEXT_PRIMARY, font_family="Inter", size=14),
        hint_style=ft.TextStyle(color=TEXT_MUTED, font_family="Inter"),
        bgcolor=BG_CARD,
        border_radius=24,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=12),
    )

    thinking_indicator = ft.Row(
        [
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ACCENT),
            ft.Text("VELLIX IA esta pensando...", color=TEXT_SECONDARY, size=12, font_family="Inter"),
        ],
        visible=False,
        alignment=ft.MainAxisAlignment.START,
    )

    def add_user_msg(text):
        messages_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, color=BG_PRIMARY, font_family="Inter", size=14),
                        bgcolor=ACCENT,
                        border_radius=18,
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                        max_width=500,
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def add_bot_msg(text):
        messages_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Markdown(
                            text,
                            selectable=True,
                            extension_set="gitHubWeb",
                            code_theme="atom-one-dark",
                        ),
                        bgcolor=BG_CARD,
                        border=ft.Border.all(1, BORDER_SUBTLE),
                        border_radius=18,
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                        max_width=500,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        page.update()

    def send_message(e):
        text = input_field.value.strip()
        if not text:
            return

        add_user_msg(text)
        input_field.value = ""
        thinking_indicator.visible = True
        page.update()

        def do_chat():
            api_key = get_setting("gemini_api_key", "")
            if not api_key:
                add_bot_msg("Configure sua API Key na aba **Configuracoes** primeiro.")
                thinking_indicator.visible = False
                page.update()
                return

            try:
                leads = get_all_leads()
                response = copilot_chat(text, leads, api_key)
                add_bot_msg(response)
            except Exception as ex:
                add_bot_msg(f"Erro: {ex}")

            thinking_indicator.visible = False
            page.update()

        threading.Thread(target=do_chat, daemon=True).start()

    input_field.on_submit = send_message
    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ACCENT,
        icon_size=20,
        on_click=send_message,
    )

    add_bot_msg(
        "Ola! Eu sou o **VELLIX IA**, seu assistente de prospeccao.\n"
        "Tenho acesso aos seus leads. Como posso ajudar?"
    )

    def suggestion_click(e):
        input_field.value = e.control.data
        send_message(None)

    suggestions = ft.Row(
        controls=[
            ft.OutlinedButton(
                "Melhores leads",
                data="Qual o melhor lead da minha base?",
                on_click=suggestion_click,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=20),
                    side=ft.BorderSide(1, BORDER_SUBTLE),
                    color=TEXT_SECONDARY,
                ),
            ),
            ft.OutlinedButton(
                "Pitch WhatsApp",
                data="Crie um pitch de WhatsApp para os top 3 leads",
                on_click=suggestion_click,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=20),
                    side=ft.BorderSide(1, BORDER_SUBTLE),
                    color=TEXT_SECONDARY,
                ),
            ),
            ft.OutlinedButton(
                "Estrategia fria",
                data="Dicas de abordagem fria B2B",
                on_click=suggestion_click,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=20),
                    side=ft.BorderSide(1, BORDER_SUBTLE),
                    color=TEXT_SECONDARY,
                ),
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=8,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY, color=ACCENT, size=24),
                        ft.Text("VELLIX IA Copilot", size=20, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                    ], spacing=10),
                    padding=ft.Padding.only(left=20, top=20, right=20, bottom=10),
                ),
                messages_list,
                ft.Container(
                    content=ft.Column([
                        thinking_indicator,
                        suggestions,
                        ft.Row([input_field, send_btn], spacing=8),
                    ], spacing=10),
                    padding=ft.Padding.all(16),
                    bgcolor=BG_PRIMARY,
                    border=ft.border.only(top=ft.BorderSide(1, BORDER_SUBTLE)),
                ),
            ],
            expand=True,
        ),
        expand=True,
        bgcolor=BG_PRIMARY,
    )
