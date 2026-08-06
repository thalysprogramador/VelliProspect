import flet as ft
import flet.fastapi as flet_fastapi
import os
import uvicorn

BG_PRIMARY = "#0A0A0A"
BG_SURFACE = "#0F0F0F"
BG_CARD = "#141414"
BORDER_SUBTLE = "#1F1F1F"
BORDER_HOVER = "#333333"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#8A8A8A"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
NAV_BG = "#0D0D0D"

def main(page: ft.Page):
    page.title = "Velli Prospect"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = BG_PRIMARY

    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
    }

    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme=ft.ColorScheme(
            primary=ACCENT,
            on_primary=BG_PRIMARY,
            surface=BG_SURFACE,
            on_surface=TEXT_PRIMARY,
        ),
    )
    page.theme_mode = ft.ThemeMode.DARK

    loaded_views = {}

    content_area = ft.Container(expand=True, bgcolor=BG_PRIMARY)

    def load_view(index):
        if index not in loaded_views:
            try:
                if index == 0:
                    from views.prospect_view import build_prospect_view
                    loaded_views[index] = build_prospect_view(page)
                elif index == 1:
                    from views.campaigns_view import build_campaigns_view
                    loaded_views[index] = build_campaigns_view(page)
                elif index == 2:
                    from views.copilot_view import build_copilot_view
                    loaded_views[index] = build_copilot_view(page)
                elif index == 3:
                    from views.settings_view import build_settings_view
                    loaded_views[index] = build_settings_view(page)
            except Exception as ex:
                print(f"[ERRO] View {index}: {ex}")
                import traceback
                traceback.print_exc()
                loaded_views[index] = ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color="#F87171"),
                        ft.Text(f"Erro ao carregar modulo: {ex}", color="#F87171", size=14),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                    padding=40, expand=True, alignment=ft.Alignment.CENTER,
                )
        return loaded_views.get(index, ft.Container(expand=True))

    def on_nav_change(e):
        idx = e.control.selected_index
        nav_rail.selected_index = idx
        nav_bar.selected_index = idx
        content_area.content = load_view(idx)
        page.update()

    nav_logo = ft.Container(
        content=ft.Column([
            ft.Image(src="logo_icon.png", width=44, height=44, fit=ft.ImageFit.CONTAIN),
            ft.Container(height=4),
            ft.Text("VELLI", size=9, weight=ft.FontWeight.W_800, color=TEXT_MUTED, font_family="Inter"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
        padding=ft.Padding.only(top=20, bottom=20),
    )

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.SELECTED,
        min_width=80,
        group_alignment=-0.85,
        bgcolor=NAV_BG,
        indicator_color=BORDER_HOVER,
        leading=nav_logo,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.ROCKET_LAUNCH_OUTLINED, selected_icon=ft.Icons.ROCKET_LAUNCH, label="Prospectar"),
            ft.NavigationRailDestination(icon=ft.Icons.FOLDER_OUTLINED, selected_icon=ft.Icons.FOLDER, label="Campanhas"),
            ft.NavigationRailDestination(icon=ft.Icons.SMART_TOY_OUTLINED, selected_icon=ft.Icons.SMART_TOY, label="VELLIX IA"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Config"),
        ],
        on_change=on_nav_change,
        selected_label_text_style=ft.TextStyle(size=10, weight=ft.FontWeight.W_600, color=ACCENT, font_family="Inter"),
        unselected_label_text_style=ft.TextStyle(size=10, color=TEXT_MUTED, font_family="Inter"),
    )

    nav_bar = ft.NavigationBar(
        selected_index=0,
        bgcolor=NAV_BG,
        indicator_color=BORDER_HOVER,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.ROCKET_LAUNCH_OUTLINED, selected_icon=ft.Icons.ROCKET_LAUNCH, label="Prospectar"),
            ft.NavigationBarDestination(icon=ft.Icons.FOLDER_OUTLINED, selected_icon=ft.Icons.FOLDER, label="Campanhas"),
            ft.NavigationBarDestination(icon=ft.Icons.SMART_TOY_OUTLINED, selected_icon=ft.Icons.SMART_TOY, label="VELLIX IA"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Config"),
        ],
        on_change=on_nav_change,
    )

    desktop_layout = ft.Row(
        controls=[nav_rail, ft.VerticalDivider(width=1, color=BORDER_SUBTLE), content_area],
        expand=True, spacing=0,
    )

    def build_layout():
        is_mobile = page.width is not None and page.width < 768
        if is_mobile:
            page.navigation_bar = nav_bar
            page.controls = [ft.SafeArea(content=content_area, expand=True)]
        else:
            page.navigation_bar = None
            page.controls = [desktop_layout]

    def on_resize(e):
        build_layout()
        page.update()

    page.on_resized = on_resize

    content_area.content = load_view(0)
    build_layout()
    page.update()


assets_dir = os.path.abspath("assets")
app = flet_fastapi.app(main, assets_dir=assets_dir)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
