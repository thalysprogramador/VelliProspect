"""
Velli Prospect V3 — Scraper Engine
Motor de busca otimizado para até 1000 leads.
Usa DuckDuckGo Search (DDGS) com paginação e deduplicação.
"""
import re
from ddgs import DDGS

# Domínios genéricos que poluem buscas B2B
BLOCKED_DOMAINS = [
    'guiamais.com.br', 'apontador.com.br', 'facebook.com', 'linkedin.com',
    'jusbrasil.com.br', 'g1.globo.com', 'wikipedia.org', 'youtube.com',
    'tripadvisor.com.br', 'mercadolivre.com.br', 'shopee.com.br', 'reclameaqui.com.br',
    'tiktok.com', 'pinterest.com', 'sympla.com.br', 'eventim.com.br', 'doctoralia.com.br',
    'olx.com.br', 'enjoei.com.br', 'magazineluiza.com.br', 'amazon.com.br',
    'yelp.com', 'glassdoor.com', 'indeed.com', 'catho.com.br', 'infojobs.com.br',
    'twitter.com', 'x.com'
]

# Fontes disponíveis com suas queries personalizadas
SOURCES = {
    "Instagram": {
        "query_template": 'site:instagram.com "{niche}" "{region}"',
        "skip_domain_filter": True
    },
    "Google Maps / Sites": {
        "query_template": '"{niche}" "{region}" contato telefone',
        "skip_domain_filter": False
    },
    "LinkedIn": {
        "query_template": 'site:linkedin.com/company "{niche}" "{region}"',
        "skip_domain_filter": True
    },
    "Google Meu Negócio": {
        "query_template": '"{niche}" "{region}" site:google.com/maps',
        "skip_domain_filter": True
    }
}


def extract_contact_info(text):
    """Extrai informações de contato do texto."""
    phone_pattern = r'(\+?55\s?)?\(?\d{2}\)?\s?(9?\d{4})[-.\\s]?(\d{4})'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    phones = re.findall(phone_pattern, text)
    emails = re.findall(email_pattern, text)

    return bool(phones), bool(emails)


def is_blocked_domain(url, block_large_portals):
    """Verifica se o URL pertence a um domínio bloqueado."""
    if not block_large_portals:
        return False
    url_lower = url.lower()
    return any(blocked in url_lower for blocked in BLOCKED_DOMAINS)


def deduplicate_leads(leads):
    """Remove leads duplicados baseado no link ou nome."""
    seen_links = set()
    seen_names = set()
    unique = []

    for lead in leads:
        link = lead.get("Link", "").lower().strip()
        name = lead.get("Nome", "").lower().strip()

        # Deduplica por link (primário) ou nome (secundário)
        if link and link in seen_links:
            continue
        if name and name in seen_names:
            continue

        if link:
            seen_links.add(link)
        if name:
            seen_names.add(name)
        unique.append(lead)

    return unique


def scrape_leads(niche, region, source, max_results=100, block_large_portals=True, on_progress=None):
    """
    Busca leads na internet.
    
    Args:
        niche: O nicho de mercado (ex: "Clínica de Estética")
        region: A região-alvo (ex: "São Paulo")
        source: A fonte de busca (chave de SOURCES)
        max_results: Número máximo de leads (até 1000)
        block_large_portals: Bloquear grandes portais genéricos
        on_progress: Callback opcional fn(current, total, lead_name) para atualizar UI
    
    Returns:
        Lista de dicts com os leads encontrados
    """
    leads = []
    max_results = min(max_results, 1000)  # Cap em 1000

    # Obter template de query baseado na fonte
    source_config = SOURCES.get(source, SOURCES["Google Maps / Sites"])
    query = source_config["query_template"].format(niche=niche, region=region)
    skip_domain = source_config["skip_domain_filter"]

    try:
        # DDGS: pegar o dobro para compensar filtros
        fetch_count = min(max_results * 3, 1500)
        results = DDGS().text(query, max_results=fetch_count)

        for i, r in enumerate(results):
            url = r.get('href', '')
            title = r.get('title', '')
            snippet = r.get('body', '')

            # Filtro de domínios bloqueados
            if not skip_domain and is_blocked_domain(url, block_large_portals):
                continue

            # Extrair contato
            combined_text = f"{snippet} {title}"
            has_phone, has_email = extract_contact_info(combined_text)

            # Limpar nome
            name = title.split(' - ')[0] if ' - ' in title else title
            name = name.split('|')[0] if '|' in name else name
            name = name.split('•')[0] if '•' in name else name
            name = name.strip()

            lead = {
                'Nome': name if name else 'Perfil Encontrado',
                'Link': url,
                'Descrição (Bio/Web)': snippet,
                'Tem Telefone?': "Sim" if has_phone else "Não",
                'Tem E-mail?': "Sim" if has_email else "Não",
                '_has_contact': has_phone or has_email
            }

            leads.append(lead)

            # Callback de progresso
            if on_progress:
                on_progress(len(leads), max_results, name[:40])

            if len(leads) >= max_results:
                break

    except Exception as e:
        print(f"Erro na extração: {e}")
        raise RuntimeError(f"Erro no provedor de busca: {e}")

    # Deduplicar antes de retornar
    leads = deduplicate_leads(leads)

    return leads[:max_results]


def get_available_sources():
    """Retorna a lista de fontes de busca disponíveis."""
    return list(SOURCES.keys())
