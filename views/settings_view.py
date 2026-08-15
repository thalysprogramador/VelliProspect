import flet as ft
import threading
from database import get_setting, set_setting

BG = "#000000"
BG_CARD = "#141415"
BG_HOVER = "#242426"
BORDER = "#2C2C2E"
TX = "#FFFFFF"
TX2 = "#A1A1A6"
TX3 = "#6E6E73"
ACC = "#2997FF"
GREEN = "#30D158"
RED = "#FF453A"
YEL = "#FFD60A"

def build_settings_view(page: ft.Page):
    current_key = get_setting("gemini_api_key", "")
    api_field = ft.TextField(value=current_key, label="Chave API Gemini", password=True, can_reveal_password=True, border_color=BORDER, focused_border_color=ACC, text_size=15, color=TX, bgcolor=BG, border_radius=12, expand=True)
    status = ft.Text("", size=14, color=TX2)

    def save(e):
        set_setting("gemini_api_key", api_field.value)
        status.value = "Credenciais salvas com sucesso."
        status.color = GREEN
        page.update()

    def test(e):
        def run():
            key = api_field.value.strip()
            if not key:
                status.value = "Por favor, insira uma chave valida."
                status.color = RED
                page.update()
                return
            status.value = "Autenticando..."
            status.color = TX2
            page.update()
            try:
                from google import genai
                client = genai.Client(api_key=key)
                r = client.models.generate_content(model="gemini-2.5-flash", contents="Responda OK")
                if r and r.text:
                    status.value = "Conexao estavel! API respondendo perfeitamente."
                    status.color = GREEN
                else:
                    status.value = "Conexao falhou (sem resposta)."
                    status.color = RED
            except Exception as ex:
                status.value = f"Falha de autenticacao: {str(ex)[:80]}"
                status.color = RED
            page.update()
        threading.Thread(target=run, daemon=True).start()

    def clear(e):
        status.value = "Recurso bloqueado nesta versao."
        status.color = YEL
        page.update()

    def section(title, icon, content_controls, border_color=BORDER):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, size=18, color=TX2), ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=TX2, font_family="Inter")], spacing=10),
                ft.Container(height=16),
            ] + content_controls, spacing=0),
            bgcolor=BG_CARD, border=ft.Border.all(1, border_color), border_radius=20, padding=32,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=20, color=f"{BG}40", offset=ft.Offset(0, 4))
        )

    return ft.Container(content=ft.Column([
        ft.Text("Ajustes do Sistema", size=32, weight=ft.FontWeight.W_600, color=TX, font_family="Inter"),
        ft.Text("Gerencie integrações e preferencias da IA.", size=16, color=TX2),
        ft.Container(height=32),
        
        section("MOTOR DE INTELIGENCIA ARTIFICIAL", ft.Icons.VPN_KEY_ROUNDED, [
            api_field,
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=BG), ft.Text("Salvar Credencial", size=14, weight=ft.FontWeight.W_600, color=BG)], spacing=8), bgcolor=ACC, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0, padding=16), on_click=save),
                ft.OutlinedButton(content=ft.Row([ft.Icon(ft.Icons.WIFI_TETHERING, size=16, color=TX2), ft.Text("Testar Conexao", size=14, weight=ft.FontWeight.W_600, color=TX2)], spacing=8), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, BORDER), padding=16), on_click=test),
            ], spacing=16),
            ft.Container(height=12),
            status,
        ]),
        
        ft.Container(height=24),
        
        section("SUPORTE & DOCUMENTACAO", ft.Icons.INFO_OUTLINE_ROUNDED, [
            ft.Text("Para obter sua chave Gemini API:\n\n1. Acesse aistudio.google.com e faca login.\n2. Clique em 'Get API Key'.\n3. Crie uma nova chave e cole no campo acima.\n\nO plano gratuito do Google oferece centenas de requisicoes diarias sem custo.", size=14, color=TX2, selectable=True, height=120),
        ]),
        
        ft.Container(height=24),
        
        section("ZONA DE PERIGO", ft.Icons.WARNING_AMBER_ROUNDED, [
            ft.OutlinedButton(content=ft.Row([ft.Icon(ft.Icons.DELETE_FOREVER, size=16, color=RED), ft.Text("Apagar Banco de Dados Local", size=14, weight=ft.FontWeight.W_600, color=RED)], spacing=8), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, f"{RED}40"), padding=16), on_click=clear),
            ft.Container(height=8),
            ft.Text("Esta acao remove todas as suas preferencias locais. Dados no Supabase (se ativo) permanecem intactos.", size=13, color=TX3),
        ], border_color=f"{RED}30"),
        
        ft.Container(height=48),
        
        ft.Container(content=ft.Column([
            ft.Image(src="logo_velli_white.png", width=160, height=48),
            ft.Text("Software proprietario Velli Marketing. Powered by Google Gemini AI.", size=12, color=TX3),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12), alignment=ft.Alignment.CENTER),
        
        ft.Container(height=48)
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0), padding=ft.Padding.symmetric(horizontal=40, vertical=32), expand=True)
