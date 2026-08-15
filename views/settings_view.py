import flet as ft
import threading
from database import get_setting, set_setting

BG = "#000000"
BG_CARD = "#1C1C1E"
BG_HOVER = "#2C2C2E"
BORDER = "#38383A"
TX = "#F5F5F7"
TX2 = "#86868B"
TX3 = "#48484A"
ACC = "#FFFFFF"
GREEN = "#30D158"
RED = "#FF453A"
YEL = "#FFD60A"

def build_settings_view(page: ft.Page):
    current_key = get_setting("gemini_api_key", "")
    api_field = ft.TextField(value=current_key, label="Chave API Gemini", password=True, can_reveal_password=True, border_color=BORDER, focused_border_color=ACC, text_size=14, color=TX, bgcolor=BG_CARD, expand=True)
    status = ft.Text("", size=13, color=TX2)

    def save(e):
        set_setting("gemini_api_key", api_field.value)
        status.value = "Salvo com sucesso!"
        status.color = GREEN
        page.update()

    def test(e):
        def run():
            key = api_field.value.strip()
            if not key:
                status.value = "Insira uma chave."
                status.color = RED
                page.update()
                return
            status.value = "Testando..."
            status.color = TX2
            page.update()
            try:
                from google import genai
                client = genai.Client(api_key=key)
                r = client.models.generate_content(model="gemini-2.5-flash", contents="Responda OK")
                if r and r.text:
                    status.value = "Conexao OK! API funcionando."
                    status.color = GREEN
                else:
                    status.value = "Sem resposta."
                    status.color = RED
            except Exception as ex:
                status.value = f"Erro: {str(ex)[:80]}"
                status.color = RED
            page.update()
        threading.Thread(target=run, daemon=True).start()

    def clear(e):
        status.value = "Em desenvolvimento."
        status.color = YEL
        page.update()

    def section(title, icon, content_controls, border_color=BORDER):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, size=16, color=TX2), ft.Text(title, size=12, weight=ft.FontWeight.W_700, color=TX2, font_family="Inter")], spacing=8),
                ft.Container(height=12),
            ] + content_controls, spacing=0),
            bgcolor=BG_CARD, border=ft.Border.all(1, border_color), border_radius=16, padding=24,
        )

    return ft.Container(content=ft.Column([
        ft.Text("Configuracoes", size=34, weight=ft.FontWeight.W_700, color=TX, font_family="Inter"),
        ft.Text("Gerencie credenciais e preferencias.", size=15, color=TX2),
        ft.Container(height=24),
        section("MOTOR DE IA", ft.Icons.KEY, [
            api_field,
            ft.Container(height=12),
            ft.Row([
                ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.SAVE, size=14, color=BG), ft.Text("Salvar", size=13, weight=ft.FontWeight.W_600, color=BG)], spacing=6), bgcolor=ACC, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), elevation=0), on_click=save),
                ft.OutlinedButton(content=ft.Row([ft.Icon(ft.Icons.WIFI_TETHERING, size=14, color=TX2), ft.Text("Testar", size=13, weight=ft.FontWeight.W_600, color=TX2)], spacing=6), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), side=ft.BorderSide(1, BORDER)), on_click=test),
            ], spacing=10),
            ft.Container(height=8),
            status,
        ]),
        ft.Container(height=16),
        section("COMO OBTER A CHAVE", ft.Icons.INFO_OUTLINE, [
            ft.Text("1. Acesse aistudio.google.com\n2. Login com Google\n3. Clique em Get API Key\n4. Crie e cole aqui\n\nGratuita. Centenas de consultas/dia.", size=14, color=TX2, selectable=True),
        ]),
        ft.Container(height=16),
        section("ZONA DE PERIGO", ft.Icons.WARNING_AMBER, [
            ft.OutlinedButton(content=ft.Row([ft.Icon(ft.Icons.DELETE_FOREVER, size=14, color=RED), ft.Text("Limpar Dados", size=13, weight=ft.FontWeight.W_600, color=RED)], spacing=6), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), side=ft.BorderSide(1, f"{RED}40")), on_click=clear),
            ft.Container(height=4),
            ft.Text("Remove todos os dados. Irreversivel.", size=12, color=TX3),
        ], border_color=f"{RED}30"),
        ft.Container(height=40),
        ft.Container(content=ft.Column([
            ft.Image(src="logo_velli.png", width=140, height=46),
            ft.Text("Powered by Google Gemini AI", size=11, color=TX3),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), alignment=ft.Alignment.CENTER),
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0), padding=ft.Padding.symmetric(horizontal=32, vertical=28), expand=True)
