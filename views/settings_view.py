import flet as ft
import threading
from google import genai
from database import get_setting, set_setting

BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BG_SURFACE = "#0F0F0F"
BORDER_SUBTLE = "#1F1F1F"
BORDER_HOVER = "#333333"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#8A8A8A"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
SUCCESS = "#34D399"
WARNING = "#FBBF24"
ERROR = "#F87171"

def build_settings_view(page: ft.Page):
    current_key = get_setting("gemini_api_key", "")

    api_key_field = ft.TextField(
        value=current_key,
        label="Chave API Gemini",
        password=True,
        can_reveal_password=True,
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        text_size=14,
        color=TEXT_PRIMARY,
        bgcolor=BG_SURFACE,
        expand=True,
    )

    status_text = ft.Text("", size=12, color=TEXT_SECONDARY, font_family="Inter")

    def save_api_key(e):
        set_setting("gemini_api_key", api_key_field.value)
        status_text.value = "Chave salva com sucesso!"
        status_text.color = SUCCESS
        page.update()

    def do_test():
        key = api_key_field.value.strip()
        if not key:
            status_text.value = "Insira uma chave para testar."
            status_text.color = ERROR
            page.update()
            return

        status_text.value = "Testando conexao..."
        status_text.color = TEXT_SECONDARY
        page.update()

        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Responda apenas OK"
            )
            if response and response.text:
                status_text.value = "Conexao bem sucedida! API funcionando."
                status_text.color = SUCCESS
            else:
                status_text.value = "Resposta vazia da API."
                status_text.color = ERROR
        except Exception as ex:
            status_text.value = f"Erro: {str(ex)[:80]}"
            status_text.color = ERROR
        page.update()

    def test_api_key(e):
        threading.Thread(target=do_test, daemon=True).start()

    def clear_data(e):
        status_text.value = "Funcionalidade em desenvolvimento."
        status_text.color = WARNING
        page.update()

    view_main = ft.Column(
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Text("Configuracoes", size=28, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY, font_family="Inter"),
                    ft.Text("Gerencie suas credenciais e preferencias.", size=14, color=TEXT_SECONDARY, font_family="Inter"),
                ], spacing=4),
                padding=ft.Padding.only(bottom=24),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.KEY, size=16, color=TEXT_SECONDARY),
                        ft.Text("MOTOR DE IA", size=11, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY, font_family="Inter"),
                    ], spacing=8),
                    ft.Container(height=12),
                    api_key_field,
                    ft.Container(height=12),
                    ft.Row([
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SAVE, size=16, color=BG_PRIMARY),
                                ft.Text("SALVAR", size=12, weight=ft.FontWeight.W_700, color=BG_PRIMARY, font_family="Inter"),
                            ], spacing=6),
                            bgcolor=ACCENT,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0),
                            on_click=save_api_key,
                        ),
                        ft.OutlinedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.WIFI_TETHERING, size=16, color=TEXT_SECONDARY),
                                ft.Text("TESTAR", size=12, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY, font_family="Inter"),
                            ], spacing=6),
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, BORDER_SUBTLE)),
                            on_click=test_api_key,
                        ),
                    ], spacing=10),
                    ft.Container(height=8),
                    status_text,
                ], spacing=0),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=14,
                padding=24,
            ),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=TEXT_SECONDARY),
                        ft.Text("COMO OBTER A CHAVE", size=11, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY, font_family="Inter"),
                    ], spacing=8),
                    ft.Container(height=8),
                    ft.Text(
                        "1. Acesse: aistudio.google.com\n"
                        "2. Faca login com sua conta Google\n"
                        "3. Clique em 'Get API Key'\n"
                        "4. Crie uma nova chave e cole aqui\n\n"
                        "A chave e gratuita e permite centenas de consultas/dia.",
                        size=13, color=TEXT_SECONDARY, font_family="Inter", selectable=True,
                    ),
                ], spacing=0),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, BORDER_SUBTLE),
                border_radius=14,
                padding=24,
            ),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER, size=16, color=ERROR),
                        ft.Text("ZONA DE PERIGO", size=11, weight=ft.FontWeight.W_700, color=ERROR, font_family="Inter"),
                    ], spacing=8),
                    ft.Container(height=12),
                    ft.OutlinedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DELETE_FOREVER, size=16, color=ERROR),
                            ft.Text("LIMPAR TODOS OS DADOS", size=12, weight=ft.FontWeight.W_600, color=ERROR, font_family="Inter"),
                        ], spacing=6),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, f"{ERROR}40")),
                        on_click=clear_data,
                    ),
                    ft.Container(height=4),
                    ft.Text("Apaga todas as campanhas e leads salvos. Nao pode ser desfeito.", size=11, color=TEXT_MUTED, font_family="Inter"),
                ], spacing=0),
                bgcolor=BG_CARD,
                border=ft.Border.all(1, f"{ERROR}20"),
                border_radius=14,
                padding=24,
            ),
            ft.Container(height=30),
            ft.Container(
                content=ft.Column([
                    ft.Text("VELLI PROSPECT V3", size=14, weight=ft.FontWeight.W_800, color=TEXT_MUTED, font_family="Inter"),
                    ft.Text("Software de Prospeccao Inteligente B2B", size=11, color=TEXT_MUTED, font_family="Inter"),
                    ft.Text("Powered by Google Gemini AI", size=10, color=TEXT_MUTED, font_family="Inter"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                alignment=ft.Alignment.CENTER,
                padding=20,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
    )

    return ft.Container(content=view_main, padding=ft.Padding.symmetric(horizontal=24, vertical=20), expand=True)
