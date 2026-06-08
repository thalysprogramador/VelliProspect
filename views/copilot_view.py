"""
Velli Prospect V3 — Copilot View (Revisado)
Assistente de IA integrado para ajudar com prospeccao e vendas.
"""
import flet as ft
import threading
from ai_evaluator import copilot_chat
from database import get_all_leads, get_setting

# Design System
BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BORDER_SUBTLE = "#2A2A2A"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"


def build_copilot_view(page: ft.Page):
    """Constroi a view do Copilot (assistente de IA)."""

    messages_list = ft.ListView(
        spacing=12,
        padding=ft.Padding.symmetric(vertical=10, horizontal=4),
        expand=True,
        auto_scroll=True,
    )

    is_thinking = False

    # Mensagem de boas-vindas
    welcome_msg = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text("V", size=14, weight=ft.FontWeight.W_800,
                                          color=BG_PRIMARY, font_family="Inter"),
                            bgcolor=ACCENT,
                            border_radius=20,
                            width=28,
                            height=28,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text("VELLIX IA", size=13, weight=ft.FontWeight.W_600,
                               color=ACCENT, font_family="Inter"),
                    ],
                    spacing=8,
                ),
                ft.Container(height=4),
                ft.Text(
                    "Ola! \U0001f44b Sou a VELLIX IA, sua inteligencia artificial focada em prospeccao.\n\n"
                    "Posso te ajudar com:\n"
                    "\u2022 Analisar seus leads e sugerir os melhores\n"
                    "\u2022 Criar pitches de vendas personalizados\n"
                    "\u2022 Dar dicas de abordagem para cada prospect\n"
                    "\u2022 Sugerir estrategias de outbound\n\n"
                    "Me pergunte qualquer coisa sobre seus leads ou estrategia de vendas!",
                    size=13, color=TEXT_SECONDARY, font_family="Inter",
                    selectable=True,
                ),
            ],
            spacing=2,
        ),
        bgcolor=BG_CARD,
        border=ft.Border.all(1, BORDER_SUBTLE),
        border_radius=14,
        padding=16,
    )
    messages_list.controls.append(welcome_msg)

    # Suggestions chips
    suggestions = [
        "Qual o melhor lead da minha base?",
        "Crie um pitch para WhatsApp",
        "Quais leads abordar primeiro?",
        "Dicas de abordagem fria",
    ]

    def on_suggestion_click(e):
        """Envia uma sugestao como mensagem."""
        input_field.value = e.control.data
        send_message(None)

    suggestion_row = ft.Row(
        controls=[
            ft.Container(
                content=ft.Text(s, size=11, color=TEXT_SECONDARY, font_family="Inter"),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                on_click=on_suggestion_click,
                data=s,
                ink=True,
            )
            for s in suggestions
        ],
        spacing=8,
        wrap=True,
    )

    # Thinking indicator
    thinking_indicator = ft.Container(
        content=ft.Row(
            controls=[
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=TEXT_MUTED),
                ft.Text("VELLIX IA processando...", size=12, color=TEXT_MUTED,
                        italic=True, font_family="Inter"),
            ],
            spacing=8,
        ),
        visible=False,
        padding=ft.Padding.only(left=8),
    )

    def add_user_message(text):
        """Adiciona uma mensagem do usuario na lista."""
        msg = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Voce", size=11, weight=ft.FontWeight.W_600,
                                   color=TEXT_MUTED, font_family="Inter"),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Text(text, size=13, color=TEXT_PRIMARY, font_family="Inter",
                            text_align=ft.TextAlign.RIGHT, selectable=True),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.END,
            ),
            bgcolor="#1A1A1A",
            border=ft.Border.all(1, "#333333"),
            border_radius=14,
            padding=14,
            alignment=ft.Alignment.CENTER_RIGHT,
        )
        messages_list.controls.append(msg)
        page.update()

    def add_copilot_message(text):
        """Adiciona uma mensagem do Copilot na lista."""
        msg = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text("V", size=10, weight=ft.FontWeight.W_800,
                                              color=BG_PRIMARY, font_family="Inter"),
                                bgcolor=ACCENT,
                                border_radius=14,
                                width=22,
                                height=22,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Text("VELLIX IA", size=11, weight=ft.FontWeight.W_600,
                                   color=ACCENT, font_family="Inter"),
                        ],
                        spacing=6,
                    ),
                    ft.Markdown(
                        text,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                        code_theme=ft.MarkdownCodeTheme.MONOKAI,
                        code_style_sheet=ft.MarkdownStyleSheet(
                            code_text_style=ft.TextStyle(
                                font_family="Courier New",
                                size=12,
                                color=TEXT_PRIMARY,
                            ),
                        ),
                    ),
                ],
                spacing=6,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_SUBTLE),
            border_radius=14,
            padding=16,
            animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        )
        messages_list.controls.append(msg)
        page.update()

    def send_message(e):
        """Envia a mensagem do usuario e obtem resposta do Copilot."""
        nonlocal is_thinking

        text = input_field.value
        if not text or not text.strip() or is_thinking:
            return

        input_field.value = ""
        is_thinking = True
        suggestion_row.visible = False
        page.update()

        add_user_message(text.strip())

        thinking_indicator.visible = True
        page.update()

        def get_response():
            nonlocal is_thinking
            import os
            from database import get_setting
            api_key = os.environ.get("GEMINI_API_KEY") or get_setting("gemini_api_key")

            if not api_key:
                thinking_indicator.visible = False
                add_copilot_message(
                    "\u26a0\ufe0f **API Key nao configurada!**\n\n"
                    "Va ate a aba **Config** (icone de engrenagem) e cole sua chave do Google AI Studio.\n\n"
                    "E gratis! Acesse [aistudio.google.com](https://aistudio.google.com) para criar a sua."
                )
                is_thinking = False
                page.update()
                return

            leads = get_all_leads()

            leads_context = []
            for lead in leads[:20]:
                leads_context.append({
                    "name": lead.get("name", ""),
                    "score": lead.get("score", 0),
                    "tags": lead.get("tags", []),
                    "description": lead.get("description", ""),
                    "decision_maker": lead.get("decision_maker", ""),
                })

            response = copilot_chat(text.strip(), leads_context, api_key)

            thinking_indicator.visible = False
            add_copilot_message(response)
            is_thinking = False
            page.update()

        thread = threading.Thread(target=get_response, daemon=True)
        thread.start()

    # Input field
    input_field = ft.TextField(
        hint_text="Mande um desafio para a VELLIX IA...",
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        hint_style=ft.TextStyle(color=TEXT_MUTED, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=24,
        filled=True,
        fill_color=BG_CARD,
        expand=True,
        on_submit=send_message,
        shift_enter=True,
    )

    send_button = ft.IconButton(
        icon=ft.Icons.SEND,
        icon_color=ACCENT,
        icon_size=20,
        tooltip="Enviar",
        on_click=send_message,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: BG_CARD},
            shape=ft.CircleBorder(),
            padding=12,
        ),
    )

    # Layout
    view_col = ft.Column(
        controls=[
            # Header
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text("V", size=16, weight=ft.FontWeight.W_800,
                                                  color=BG_PRIMARY, font_family="Inter"),
                                    bgcolor=ACCENT,
                                    border_radius=24,
                                    width=36,
                                    height=36,
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("VELLIX IA", size=20, weight=ft.FontWeight.W_700,
                                               color=TEXT_PRIMARY, font_family="Inter"),
                                        ft.Text("Inteligencia Oficial B2B", size=12,
                                               color=TEXT_SECONDARY, font_family="Inter"),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=12,
                        ),
                    ],
                ),
                padding=ft.Padding.only(bottom=12),
            ),

            # Messages
            messages_list,

            # Suggestions
            suggestion_row,

            # Thinking
            thinking_indicator,

            ft.Container(height=8),

            # Input bar
            ft.Container(
                content=ft.Row(
                    controls=[input_field, send_button],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=BG_PRIMARY,
                padding=ft.Padding.only(top=8, bottom=8),
            ),
        ],
        expand=True,
        spacing=0,
    )

    view = ft.Container(
        content=view_col,
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        expand=True,
    )

    return view