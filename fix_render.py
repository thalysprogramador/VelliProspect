"""
Script para reconfigurar o serviço Render de Docker para Python nativo.
Precisa de uma API Key do Render. 
Se não tiver, o caminho é deletar o serviço e recriar.
"""
import requests

# O Service ID visível no dashboard do Render
SERVICE_ID = "srv-d7nvkovavr4c73ffthevg"

# Precisamos da API Key do Render para isso.
# Vamos tentar primeiro sem API Key, usando a abordagem de deletar e recriar.

print("""
╔══════════════════════════════════════════════════════════════╗
║  AÇÃO NECESSÁRIA NO RENDER DASHBOARD                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  O serviço atual está configurado como "Docker".             ║
║  Precisamos trocá-lo para "Python nativo".                   ║
║                                                              ║
║  OPÇÃO MAIS RÁPIDA (2 minutos):                             ║
║                                                              ║
║  1. Acesse: https://dashboard.render.com                     ║
║  2. Clique no serviço "velli-prospect"                       ║
║  3. No menu esquerdo, clique em "Settings"                   ║
║  4. Role até "Delete Service" e APAGUE o serviço             ║
║  5. Depois, clique em "+ New" > "Blueprint"                  ║
║  6. Conecte ao repo "VelliProspect" (branch: main)           ║
║  7. O Render vai ler o render.yaml e criar com Python!       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
