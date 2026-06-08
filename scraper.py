"""
Velli Prospect V3 — Scraper Engine (Revisado)
Motor de busca otimizado para ate 1000 leads.
Usa DuckDuckGo Search (DDGS) com paginacao, deduplicacao e multi-fonte.
"""
import re
from ddgs import DDGS

# Dominios genericos que poluem buscas B2B
BLOCKED_DOMAINS = [
    'guiamais.com.br', 'apontador.com.br', 'facebook.com', 'linkedin.com',
    'jusbrasil.com.br', 'g1.globo.com', 'wikipedia.org', 'youtube.com',
    'tripadvisor.com.br', 'mercadolivre.com.br', 'shopee.com.br', 'reclameaqui.com.br',
    'tiktok.com', 'pinterest.com', 'sympla.com.br', 'eventim.com.br', 'doctoralia.com.br',
    'olx.com.br', 'enjoei.com.br', 'magazineluiza.com.br', 'amazon.com.br',
    'yelp.com', 'glassdoor.com', 'glassdoor.com.br', 'indeed.com', 'indeed.com.br',
    'catho.com.br', 'infojobs.com.br', 'vagas.com.br', 'trampos.co',
    'twitter.com', 'x.com', 'gov.br',
]

# Fontes disponiveis com suas queries personalizadas
SOURCES = {
    "Instagram": {
        "query_template": 'site:instagram.com "{niche}" "{region}"',
        "skip_domain_filter": True,
    },
    "Google Maps / Sites": {
        "query_template": '"{niche}" "{region}" contato telefone',
        "skip_domain_filter": False,
    },
    "LinkedIn": {
        "query_template": 'site:linkedin.com/company "{niche}" "{region}"',
        "skip_domain_filter": True,
    },
    "Google Meu Negocio": {
        "query_template": '"{niche}" "{region}" site:google.com/maps',
        "skip_domain_filter": True,
    },
    "Facebook": {
        "query_template": 'site:facebook.com "{niche}" "{region}"',
        "skip_domain_filter": True,
    },
    "Sites Proprios": {
        "query_template": '"{niche}" "{region}" contato site:.com.br',
        "skip_domain_filter": False,
    },
}

ALL_SOURCES_KEY = "Todas as Fontes"


def extract_contact_info(text):
    """Extrai informacoes de contato do texto (telefone e e-mail)."""
    phone_patterns = [
        r'(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)(?:9\s?\d{4})[\s.\-]?\d{4}',
        r'(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)(?:\d{4})[\s.\-]?\d{4}',
        r'(?:whatsapp|wpp|zap)[\s:]*(?:\+?55\s?)?\(?\d{2}\)?\s?\d{4,5}[\-\s.]?\d{4}',
    ]
    email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'

    has_phone = False
    for pattern in phone_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            has_phone = True
            break

    emails = re.findall(email_pattern, text, re.IGNORECASE)
    filtered_emails = [e for e in emails if not any(
        x in e.lower() for x in ['noreply', 'no-reply', 'example.com', 'sentry', 'cloudflare']
    )]
    has_email = bool(filtered_emails)

    return has_phone, has_email


def is_blocked_domain(url, block_large_portals):
    """Verifica se o URL pertence a um dominio bloqueado."""
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

        if link and link in seen_links:
            continue
        if name and len(name) > 5 and name in seen_names:
            continue

        if link:
            seen_links.add(link)
        if name:
            seen_names.add(name)
        unique.append(lead)

    return unique


def _clean_name(title):
    """Limpa e extrai o nome real de um titulo de resultado de busca."""
    for sep in [' - ', ' | ', ' \u2014 ', ' \u00b7 ', ' :: ']:
        if sep in title:
            title = title.split(sep)[0]
    return title.strip() or "Perfil Encontrado"


def _scrape_single_source(niche, region, source_key, max_results, block_large_portals, on_progress=None):
    """Busca leads de uma unica fonte."""
    leads = []
    source_config = SOURCES.get(source_key, SOURCES["Google Maps / Sites"])
    query = source_config["query_template"].format(niche=niche, region=region)
    skip_domain = source_config["skip_domain_filter"]

    try:
        fetch_count = min(max_results * 3, 1500)
        results = DDGS().text(query, max_results=fetch_count)

        for r in results:
            url = r.get('href', '')
            title = r.get('title', '')
            snippet = r.get('body', '')

            if not skip_domain and is_blocked_domain(url, block_large_portals):
                continue

            combined_text = f"{snippet} {title} {url}"
            has_phone, has_email = extract_contact_info(combined_text)

            name = _clean_name(title)

            lead = {
                'Nome': name,
                'Link': url,
                'Descricao (Bio/Web)': snippet,
                'Tem Telefone?': "Sim" if has_phone else "Nao",
                'Tem E-mail?': "Sim" if has_email else "Nao",
                '_has_contact': has_phone or has_email,
                '_source': source_key,
            }
            leads.append(lead)

            if on_progress:
                on_progress(len(leads), max_results, name[:40])

            if len(leads) >= max_results:
                break

    except Exception as e:
        print(f"Erro na extracao ({source_key}): {e}")
        if not leads:
            raise RuntimeError(f"Erro no provedor de busca ({source_key}): {e}")

    return leads


def scrape_leads(niche, region, source, max_results=100, block_large_portals=True, on_progress=None):
    """
    Busca leads na internet.
    """
    max_results = min(max_results, 1000)

    if source == ALL_SOURCES_KEY:
        all_leads = []
        source_keys = list(SOURCES.keys())
        per_source = max(max_results // len(source_keys), 20)

        for src_key in source_keys:
            if len(all_leads) >= max_results:
                break

            remaining = max_results - len(all_leads)
            batch_size = min(per_source, remaining)

            try:
                batch = _scrape_single_source(
                    niche, region, src_key, batch_size,
                    block_large_portals, on_progress
                )
                all_leads.extend(batch)
            except Exception as e:
                print(f"Fonte '{src_key}' falhou, continuando: {e}")
                continue

        all_leads = deduplicate_leads(all_leads)
        return all_leads[:max_results]
    else:
        leads = _scrape_single_source(
            niche, region, source, max_results,
            block_large_portals, on_progress
        )
        leads = deduplicate_leads(leads)
        return leads[:max_results]


def get_available_sources():
    """Retorna a lista de fontes de busca disponiveis."""
    return list(SOURCES.keys()) + [ALL_SOURCES_KEY]