import flet as ft
import flet.fastapi as flet_fastapi
import os
import uvicorn

# Pre-load views for INSTANT navigation
from views.prospect_view import build_prospect_view
from views.campaigns_view import build_campaigns_view
from views.copilot_view import build_copilot_view
from views.settings_view import build_settings_view

# Apple-Inspired Design Tokens
BG = "#000000"
BG_SEC = "#0A0A0A"
BG_CARD = "#141415"
BG_HOVER = "#242426"
BORDER = "#2C2C2E"
TX = "#FFFFFF"
TX2 = "#A1A1A6"
TX3 = "#6E6E73"
ACC = "#2997FF"
GREEN = "#30D158"
YEL = "#FFD60A"
RED = "#FF453A"

def main(page: ft.Page):
    page.title = "Velli Prospect"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = BG
    page.fonts = {"Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"}
    page.theme = ft.Theme(font_family="Inter", color_scheme=ft.ColorScheme(primary=ACC, on_primary=BG, surface=BG_SEC, on_surface=TX))
    page.theme_mode = ft.ThemeMode.DARK

    views_cache = {}
    content = ft.Container(expand=True, bgcolor=BG)

    def load_view(idx):
        if idx not in views_cache:
            try:
                if idx == 0: views_cache[idx] = build_prospect_view(page)
                elif idx == 1: views_cache[idx] = build_campaigns_view(page)
                elif idx == 2: views_cache[idx] = build_copilot_view(page)
                elif idx == 3: views_cache[idx] = build_settings_view(page)
            except Exception as ex:
                import traceback; traceback.print_exc()
                views_cache[idx] = ft.Container(content=ft.Text(f"Erro: {ex}", color=RED), padding=40, expand=True)
        return views_cache.get(idx, ft.Container(expand=True))

    def nav_change(e):
        idx = e.control.selected_index
        rail.selected_index = idx
        bar.selected_index = idx
        content.content = load_view(idx)
        page.update()

    logo_widget = ft.Container(
        content=ft.Image(src="logo_velli_white.png", width=140, height=45),
        padding=ft.Padding.only(top=32, bottom=32, left=0, right=0),
        alignment=ft.Alignment.CENTER,
    )

    dests = [
        ft.NavigationRailDestination(icon=ft.Icons.ROCKET_LAUNCH_OUTLINED, selected_icon=ft.Icons.ROCKET_LAUNCH, label="Prospectar"),
        ft.NavigationRailDestination(icon=ft.Icons.FOLDER_OUTLINED, selected_icon=ft.Icons.FOLDER, label="Campanhas"),
        ft.NavigationRailDestination(icon=ft.Icons.AUTO_AWESOME_OUTLINED, selected_icon=ft.Icons.AUTO_AWESOME, label="VELLIX IA"),
        ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Config"),
    ]

    rail = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.SELECTED,
        min_width=96, group_alignment=-1.0, bgcolor=BG_SEC, indicator_color=BG_HOVER,
        leading=logo_widget, destinations=dests, on_change=nav_change,
        selected_label_text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_600, color=ACC),
        unselected_label_text_style=ft.TextStyle(size=11, color=TX3),
    )

    bar = ft.NavigationBar(
        selected_index=0, bgcolor=BG_SEC, indicator_color=BG_HOVER,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.ROCKET_LAUNCH_OUTLINED, selected_icon=ft.Icons.ROCKET_LAUNCH, label="Prospectar"),
            ft.NavigationBarDestination(icon=ft.Icons.FOLDER_OUTLINED, selected_icon=ft.Icons.FOLDER, label="Campanhas"),
            ft.NavigationBarDestination(icon=ft.Icons.AUTO_AWESOME_OUTLINED, selected_icon=ft.Icons.AUTO_AWESOME, label="VELLIX IA"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Config"),
        ],
        on_change=nav_change,
    )

    desktop = ft.Row(controls=[rail, ft.VerticalDivider(width=1, color=BORDER), content], expand=True, spacing=0)

    def layout():
        mobile = page.width is not None and page.width < 768
        if mobile:
            page.navigation_bar = bar
            page.controls = [ft.SafeArea(content=content, expand=True)]
        else:
            page.navigation_bar = None
            page.controls = [desktop]

    page.on_resized = lambda e: (layout(), page.update())
    # Pre-render all views in background so navigation is instant
    for i in range(4): load_view(i)
    content.content = load_view(0)
    layout()
    page.update()

assets_dir = os.path.abspath("assets")
app = flet_fastapi.app(main, assets_dir=assets_dir)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)