
import shutil
import re

# 1. Fix the logo
shutil.copy(r"C:\Users\thaly\.gemini\antigravity\brain\388b2144-0964-4c33-ad3f-4eecca5d7c85\.user_uploaded\media_1786759174595.png", "assets/logo_icon.png")

# 2. Fix the tags_row tuple bug and btn_export colors in campaigns_view.py
with open("views/campaigns_view.py", "r", encoding="utf-8") as f:
    c = f.read()

# Fix the trailing comma bug
c = c.replace("tags_row = ft.Row([_tag(t) for t in l.get(\"tags\", [])], wrap=True, spacing=6),", "tags_row = ft.Row([_tag(t) for t in l.get(\"tags\", [])], wrap=True, spacing=6)")

# Fix the export button colors
btn_orig = "content=ft.Row([ft.Icon(ft.Icons.DOWNLOAD_ROUNDED,  size=16), ft.Text(\"Exportar Planilha (XLSX)\",  size=13, weight=ft.FontWeight.W_600)], spacing=6)"
btn_new = "content=ft.Row([ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=16, color=TX), ft.Text(\"Exportar Planilha (XLSX)\", size=13, weight=ft.FontWeight.W_600, color=TX)], spacing=6)"
c = c.replace(btn_orig, btn_new)

with open("views/campaigns_view.py", "w", encoding="utf-8") as f:
    f.write(c)

print("Bugs fixed successfully")

