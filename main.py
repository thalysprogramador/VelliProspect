"""
Velli Prospect V3 — Main Entry Point
Aplicativo de prospecção B2B profissional com interface nativa.
Roda no PC (Windows/Mac/Linux) e no celular (Android APK via Flet).
"""
import flet as ft
from views.prospect_view import build_prospect_view
from views.campaigns_view import build_campaigns_view
from views.copilot_view import build_copilot_view
from views.settings_view import build_settings_view

# ─── Design Tokens ───────────────────────────────────────────
BG_PRIMARY = "#0A0A0A"
BG_SURFACE = "#0F0F0F"
BG_CARD = "#141414"
BORDER_SUBTLE = "#2A2A2A"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#555555"
ACCENT = "#FFFFFF"
NAV_BG = "#0C0C0C"
NAV_BORDER = "#1A1A1A"


def main(page: ft.Page):
    # ─── Page Setup ───────────────────────────────────────
    page.title = "VELLI PROSPECT V3"
    page.bgcolor = BG_PRIMARY
    page.padding = 0
    page.spacing = 0
    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
    }
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ACCENT,
            on_primary=BG_PRIMARY,
            surface=BG_SURFACE,
            on_surface=TEXT_PRIMARY,
            surface_container=BG_CARD,
            on_surface_variant=TEXT_SECONDARY,
            outline=BORDER_SUBTLE,
        ),
        font_family="Inter",
    )
    page.theme_mode = ft.ThemeMode.DARK

    # ─── Content Area ─────────────────────────────────────
    content_area = ft.Container(
        expand=True,
        padding=0, # Removido para permitir overlays (Gavetas) de tela cheia
        bgcolor=BG_PRIMARY,
    )

    # ─── Views ────────────────────────────────────────────
    views = {}
    current_index = 0

    def get_or_build_view(index):
        """Lazy-load views: only build when first accessed."""
        if index not in views:
            if index == 0:
                views[index] = build_prospect_view(page)
            elif index == 1:
                views[index] = build_campaigns_view(page)
            elif index == 2:
                views[index] = build_copilot_view(page)
            elif index == 3:
                views[index] = build_settings_view(page)
        return views[index]

    def switch_view(index):
        """Troca a view ativa com animação."""
        nonlocal current_index
        current_index = index
        
        v = get_or_build_view(index)
        if hasattr(v, "on_active"):
            v.on_active()
            
        content_area.content = v
        nav_rail.selected_index = index
        nav_bar.selected_index = index
        page.update()

    def on_nav_change(e):
        """Handler para mudança de navegação."""
        switch_view(e.control.selected_index)

    # ─── Navigation Rail (Desktop) ────────────────────────
    nav_destinations = [
        ft.NavigationRailDestination(
            icon=ft.Icons.ROCKET_LAUNCH_OUTLINED,
            selected_icon=ft.Icons.ROCKET_LAUNCH,
            label="Prospectar",
        ),
        ft.NavigationRailDestination(
            icon=ft.Icons.FOLDER_OUTLINED,
            selected_icon=ft.Icons.FOLDER,
            label="Campanhas",
        ),
        ft.NavigationRailDestination(
            icon=ft.Icons.SMART_TOY_OUTLINED,
            selected_icon=ft.Icons.SMART_TOY,
            label="VELLIX IA",
        ),
        ft.NavigationRailDestination(
            icon=ft.Icons.SETTINGS_OUTLINED,
            selected_icon=ft.Icons.SETTINGS,
            label="Config",
        ),
    ]

    # Logo for NavigationRail leading
    nav_logo = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text("V", size=20, weight=ft.FontWeight.W_900,
                                  color=BG_PRIMARY, font_family="Inter"),
                    bgcolor=ACCENT,
                    border_radius=12,
                    width=40,
                    height=40,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(height=4),
                ft.Text("VELLI", size=9, weight=ft.FontWeight.W_800,
                       color=TEXT_MUTED, font_family="Inter"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        padding=ft.Padding.only(top=16, bottom=16),
    )

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.SELECTED,
        min_width=72,
        min_extended_width=180,
        group_alignment=-0.85,
        bgcolor=NAV_BG,
        indicator_color=f"{ACCENT}15",
        leading=nav_logo,
        destinations=nav_destinations,
        on_change=on_nav_change,
        selected_label_text_style=ft.TextStyle(
            size=10, weight=ft.FontWeight.W_600, color=ACCENT, font_family="Inter",
        ),
        unselected_label_text_style=ft.TextStyle(
            size=10, color=TEXT_MUTED, font_family="Inter",
        ),
    )

    # ─── Navigation Bar (Mobile) ──────────────────────────
    nav_bar = ft.NavigationBar(
        selected_index=0,
        bgcolor=NAV_BG,
        indicator_color=f"{ACCENT}15",
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.ROCKET_LAUNCH_OUTLINED,
                selected_icon=ft.Icons.ROCKET_LAUNCH,
                label="Prospectar",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.FOLDER_OUTLINED,
                selected_icon=ft.Icons.FOLDER,
                label="Campanhas",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SMART_TOY_OUTLINED,
                selected_icon=ft.Icons.SMART_TOY,
                label="VELLIX IA",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Config",
            ),
        ],
        on_change=on_nav_change,
    )

    # ─── Responsive Layout ────────────────────────────────
    def build_layout():
        """Constrói o layout responsivo: Rail no desktop, Bar no mobile."""
        is_mobile = page.width is not None and page.width < 768

        if is_mobile:
            # Mobile: Bottom NavigationBar
            page.navigation_bar = nav_bar
            page.controls = [
                ft.SafeArea(
                    content=content_area,
                    expand=True,
                ),
            ]
        else:
            # Desktop: Left NavigationRail
            page.navigation_bar = None
            page.controls = [
                ft.Row(
                    controls=[
                        nav_rail,
                        ft.VerticalDivider(width=1, color=NAV_BORDER),
                        content_area,
                    ],
                    expand=True,
                    spacing=0,
                ),
            ]

    def on_resize(e):
        """Reconstrói o layout quando a janela muda de tamanho."""
        build_layout()
        page.update()

    page.on_resized = on_resize
    page.window.width = 1200
    page.window.height = 800

    # ─── Initial Load ─────────────────────────────────────
    switch_view(0)
    build_layout()
    page.update()


# ─── Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    ft.run(main, host="0.0.0.0", port=port, assets_dir="assets")
