"""
Velli Prospect V3 — Settings View
Configurações do aplicativo (API Key, preferências).
"""
import flet as ft
from database import get_setting, set_setting

# ─── Design System ───────────────────────────────────────────
BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BORDER_SUBTLE = "#2A2A2A"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
SUCCESS = "#4ADE80"
ERROR = "#F87171"


def build_settings_view(page: ft.Page):
    """Constrói a view de configurações."""

    # Carregar configurações salvas
    saved_key = get_setting("gemini_api_key", "")

    api_key_field = ft.TextField(
        label="Gemini API Key",
        value=saved_key,
        password=True,
        can_reveal_password=True,
        hint_text="Cole aqui sua chave do Google AI Studio...",
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, font_family="Inter"),
        text_style=ft.TextStyle(font_family="Inter"),
        border_radius=10,
        filled=True,
        fill_color=BG_CARD,
    )

    status_text = ft.Text("", size=12, font_family="Inter")

    def save_api_key(e):
        """Salva a API Key no banco local."""
        key = api_key_field.value.strip()
        if not key:
            status_text.value = "⚠️ A chave não pode estar vazia."
            status_text.color = ERROR
            page.update()
            return

        set_setting("gemini_api_key", key)
        status_text.value = "✅ API Key salva com sucesso!"
        status_text.color = SUCCESS

        page.snack_bar = ft.SnackBar(
            content=ft.Text("🔑 API Key configurada!", color=TEXT_PRIMARY, font_family="Inter"),
            bgcolor=BG_CARD,
        )
        page.snack_bar.open = True
        page.update()

    def test_api_key(e):
        """Testa se a API Key funciona."""
        key = api_key_field.value.strip()
        if not key:
            status_text.value = "⚠️ Insira uma chave primeiro."
            status_text.color = ERROR
            page.update()
            return

        status_text.value = "⏳ Testando conexão..."
        status_text.color = TEXT_SECONDARY
        page.update()

        try:
            from google import genai
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents='Responda apenas: "OK"',
            )
            if response.text:
                status_text.value = f"✅ Conexão OK! Resposta: {response.text.strip()[:30]}"
                status_text.color = SUCCESS
            else:
                status_text.value = "⚠️ A API respondeu, mas sem conteúdo."
                status_text.color = ERROR
        except Exception as ex:
            status_text.value = f"❌ Erro: {str(ex)[:80]}"
            status_text.color = ERROR

        page.update()

    def clear_data(e):
        """Limpa todos os dados locais."""
        from database import get_connection
        conn = get_connection()
        conn.execute("DELETE FROM leads")
        conn.execute("DELETE FROM campaigns")
        conn.commit()
        conn.close()

        page.snack_bar = ft.SnackBar(
            content=ft.Text("🗑️ Dados limpos!", color=TEXT_PRIMARY, font_family="Inter"),
            bgcolor=BG_CARD,
        )
        page.snack_bar.open = True
        page.update()

    view = ft.Column(
        controls=[
            # Header
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Configurações", size=24, weight=ft.FontWeight.W_700,
                               color=TEXT_PRIMARY, font_family="Inter"),
                        ft.Text("Gerencie suas credenciais e preferências",
                               size=13, color=TEXT_SECONDARY, font_family="Inter"),
                    ],
                    spacing=4,
                ),
                padding=ft.Padding.only(bottom=20),
            ),

            # API Key section
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.KEY, size=16, color=TEXT_SECONDARY),
                                ft.Text("MOTOR DE IA", size=11, weight=ft.FontWeight.W_600,
                                        color=TEXT_SECONDARY, font_family="Inter"),
                            ],
                            spacing=8,
                        ),
                        ft.Container(height=8),
                        api_key_field,
                        ft.Container(height=8),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.SAVE, size=16, color=BG_PRIMARY),
                                            ft.Text("SALVAR", size=12, weight=ft.FontWeight.W_600,
                                                    color=BG_PRIMARY, font_family="Inter"),
                                        ],
                                        spacing=6,
                                    ),
                                    bgcolor=ACCENT,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        padding=ft.Padding.symmetric(vertical=12, horizontal=20),
                                        elevation=0,
                                    ),
                                    on_click=save_api_key,
                                ),
                                ft.OutlinedButton(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.WIFI_TETHERING, size=16, color=TEXT_SECONDARY),
                                            ft.Text("TESTAR", size=12, weight=ft.FontWeight.W_600,
                                                    color=TEXT_SECONDARY, font_family="Inter"),
                                        ],
                                        spacing=6,
                                    ),
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        padding=ft.Padding.symmetric(vertical=12, horizontal=20),
                                        side=ft.BorderSide(1, BORDER_SUBTLE),
                                    ),
                                    on_click=test_api_key,
                                ),
                            ],
                            spacing=10,
                        ),
                        status_text,
                    ],
                    spacing=4,
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=14,
                padding=20,
            ),

            ft.Container(height=16),

            # Info section
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=TEXT_SECONDARY),
                                ft.Text("COMO OBTER A CHAVE", size=11, weight=ft.FontWeight.W_600,
                                        color=TEXT_SECONDARY, font_family="Inter"),
                            ],
                            spacing=8,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            "1. Acesse: aistudio.google.com\n"
                            "2. Faça login com sua conta Google\n"
                            "3. Clique em 'Get API Key'\n"
                            "4. Crie uma nova chave e cole aqui\n\n"
                            "💡 A chave é gratuita e permite centenas de consultas/dia.",
                            size=12, color=TEXT_SECONDARY, font_family="Inter",
                            selectable=True,
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=14,
                padding=20,
            ),

            ft.Container(height=16),

            # Danger zone
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.WARNING_AMBER, size=16, color=ERROR),
                                ft.Text("ZONA DE PERIGO", size=11, weight=ft.FontWeight.W_600,
                                        color=ERROR, font_family="Inter"),
                            ],
                            spacing=8,
                        ),
                        ft.Container(height=8),
                        ft.OutlinedButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.DELETE_FOREVER, size=16, color=ERROR),
                                    ft.Text("LIMPAR TODOS OS DADOS", size=12,
                                            weight=ft.FontWeight.W_600, color=ERROR, font_family="Inter"),
                                ],
                                spacing=6,
                            ),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=ft.Padding.symmetric(vertical=12, horizontal=20),
                                side=ft.BorderSide(1, f"{ERROR}40"),
                            ),
                            on_click=clear_data,
                        ),
                        ft.Text("Apaga todas as campanhas e leads salvos. Isso não pode ser desfeito.",
                               size=11, color=TEXT_MUTED, font_family="Inter"),
                    ],
                    spacing=4,
                ),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, f"{ERROR}20"),
                border_radius=14,
                padding=20,
            ),

            ft.Container(height=20),

            # Footer
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("VELLI PROSPECT V3", size=14, weight=ft.FontWeight.W_800,
                               color=TEXT_MUTED, font_family="Inter"),
                        ft.Text("Software de Prospecção Inteligente B2B",
                               size=11, color=TEXT_MUTED, font_family="Inter"),
                        ft.Text("Powered by Google Gemini AI",
                               size=10, color=TEXT_MUTED, font_family="Inter"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                alignment=ft.Alignment.CENTER,
                padding=20,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
    )

    return view
