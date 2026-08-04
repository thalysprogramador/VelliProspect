import flet as ft
import os
from database import get_setting, set_setting, get_connection

BG_PRIMARY = "#0A0A0A"
BG_CARD = "#141414"
BORDER_SUBTLE = "#2A2A2A"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
SUCCESS = "#4ADE80"
WARNING = "#FBBF24"
ERROR = "#F87171"

def build_settings_view(page: ft.Page):
    api_key_field = ft.TextField(
        label="API Key do Gemini",
        password=True,
        can_reveal_password=True,
        value=get_setting("gemini_api_key", ""),
        border_color=BORDER_SUBTLE,
        focused_border_color=ACCENT,
        text_style=ft.TextStyle(font_family="Inter", size=14, color=TEXT_PRIMARY),
        label_style=ft.TextStyle(font_family="Inter", color=TEXT_SECONDARY),
        expand=True
    )

    status_text = ft.Text(size=12, font_family="Inter")

    def save_api_key(e):
        set_setting("gemini_api_key", api_key_field.value)
        status_text.value = "Chave salva com sucesso!"
        status_text.color = SUCCESS
        page.update()

    def test_api_key(e):
        key = api_key_field.value
        if not key:
            status_text.value = "Insira uma chave primeiro."
            status_text.color = WARNING
            page.update()
            return
            
        status_text.value = "Testando conexao..."
        status_text.color = TEXT_SECONDARY
        page.update()
        
        try:
            from google import genai
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Responda apenas 'OK'"
            )
            if "OK" in response.text:
                status_text.value = "Conexao estabelecida com sucesso! O motor de IA esta pronto."
                status_text.color = SUCCESS
            else:
                status_text.value = "Resposta inesperada da IA."
                status_text.color = WARNING
        except Exception as ex:
            status_text.value = f"Erro na chave: {ex}"
            status_text.color = ERROR
            
        page.update()

    def clear_data(e):
        try:
            supabase = get_connection()
            supabase.table("leads").delete().neq("id", 0).execute()
            supabase.table("campaigns").delete().neq("id", 0).execute()
            status_text.value = "Todos os dados foram apagados."
            status_text.color = SUCCESS
        except Exception as ex:
            status_text.value = f"Erro ao apagar dados: {ex}"
            status_text.color = ERROR
        page.update()

    view_main = ft.Column(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Configuracoes", size=24, weight=ft.FontWeight.W_700,
                               color=TEXT_PRIMARY, font_family="Inter"),
                        ft.Text("Gerencie suas credenciais e preferencias",
                               size=13, color=TEXT_SECONDARY, font_family="Inter"),
                    ],
                    spacing=4,
                ),
                padding=ft.Padding.only(bottom=20),
            ),
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
                            "2. Faca login com sua conta Google\n"
                            "3. Clique em 'Get API Key'\n"
                            "4. Crie uma nova chave e cole aqui\n\n"
                            "A chave e gratuita e permite centenas de consultas/dia.",
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
                        ft.Text("Apaga todas as campanhas e leads salvos. Isso nao pode ser desfeito.",
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
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("VELLI PROSPECT V3", size=14, weight=ft.FontWeight.W_800,
                               color=TEXT_MUTED, font_family="Inter"),
                        ft.Text("Software de Prospeccao Inteligente B2B",
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

    return ft.Container(
        content=view_main,
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
        expand=True,
    )