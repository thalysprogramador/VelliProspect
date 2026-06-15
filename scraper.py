"""
Velli Prospect V3 — Scraper Engine (Revisado v2)
Motor de busca robusto com fallback para servidores cloud.
Usa DuckDuckGo Search (DDGS) com proxy automatico, retry e tratamento de erro visivel.
"""
import re
import time
import traceback

# Tenta importar o pacote correto
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

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
        "query_template": 'site:instagram.com {niche} {region}',
        "skip_domain_filter": True,
    },
    "Google Maps / Sites": {
        "query_template": '{niche} {region} contato telefone',
        "skip_domain_filter": False,
    },
    "LinkedIn": {
        "query_template": 'site:linkedin.com/company {niche} {region}',
        "skip_domain_filter": True,
    },
    "Google Meu Negocio": {
        "query_template": '{niche} {region} site:google.com/maps',
        "skip_domain_filter": True,
    },
    "Facebook": {
        "query_template": 'site:facebook.com {niche} {region}',
        "skip_domain_filter": True,
    },
    "Sites Proprios": {
        "query_template": '{niche} {region} contato site:.com.br',
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


def _ddgs_search_with_retry(query, max_results, max_retries=3):
    """Executa busca DDGS com retry e proxy automatico para servidores cloud."""
    last_error = None

    # Estrategias de busca: sem proxy, com proxy lite, com proxy
    proxy_options = [None, "socks5://0.0.0.0:0"]  # None = sem proxy

    for attempt in range(max_retries):
        for proxy in proxy_options:
            try:
                # Tenta criar o cliente DDGS
                if proxy and proxy != "socks5://0.0.0.0:0":
                    ddgs = DDGS(proxy=proxy)
                else:
                    ddgs = DDGS()

                results = list(ddgs.text(query, max_results=max_results))

                if results:
                    print(f"[Scraper] Busca OK: {len(results)} resultados (tentativa {attempt+1})")
                    return results
                else:
                    print(f"[Scraper] Busca vazia para: {query[:60]}... (tentativa {attempt+1})")
                    # Se veio vazio, pode ser rate limit - espera um pouco
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    continue

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                print(f"[Scraper] Erro tentativa {attempt+1}: {type(e).__name__}: {str(e)[:100]}")

                # Se for rate limit do DuckDuckGo, espera mais
                if "ratelimit" in error_str or "429" in error_str or "too many" in error_str:
                    wait = 5 * (attempt + 1)
                    print(f"[Scraper] Rate limit detectado, aguardando {wait}s...")
                    time.sleep(wait)
                    break  # Sai do loop de proxy, vai pro proximo attempt

                # Se for erro de conexao/DNS, tenta o proximo proxy
                if "connect" in error_str or "name" in error_str or "dns" in error_str:
                    continue

                # Outros erros, espera e tenta de novo
                time.sleep(2)
                break

    # Se todas as tentativas falharam, loga o erro e retorna lista vazia
    print(f"[Scraper] FALHA TOTAL apos {max_retries} tentativas. Ultimo erro: {last_error}")
    return []


def _scrape_single_source(niche, region, source_key, max_results, block_large_portals, on_progress=None):
    """Busca leads de uma unica fonte."""
    leads = []
    source_config = SOURCES.get(source_key, SOURCES["Google Maps / Sites"])
    query = source_config["query_template"].format(niche=niche, region=region)
    skip_domain = source_config["skip_domain_filter"]

    print(f"[Scraper] Buscando: '{query}' (fonte: {source_key}, max: {max_results})")

    try:
        fetch_count = min(max_results * 3, 300)
        results = _ddgs_search_with_retry(query, fetch_count)

        if not results:
            print(f"[Scraper] Nenhum resultado retornado para fonte '{source_key}'")
            return leads

        print(f"[Scraper] {len(results)} resultados brutos recebidos de '{source_key}'")

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
        print(f"[Scraper] Erro CRITICO na extracao ({source_key}): {e}")
        traceback.print_exc()

    print(f"[Scraper] Fonte '{source_key}' retornou {len(leads)} leads processados")
    return leads


def scrape_leads(niche, region, source, max_results=100, block_large_portals=True, on_progress=None):
    """
    Busca leads na internet.
    """
    max_results = min(max_results, 1000)
    print(f"\n{'='*60}")
    print(f"[Scraper] INICIO: nicho='{niche}', regiao='{region}', fonte='{source}', max={max_results}")
    print(f"{'='*60}")

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
                print(f"[Scraper] Total acumulado: {len(all_leads)} leads")
            except Exception as e:
                print(f"[Scraper] Fonte '{src_key}' falhou, continuando: {e}")
                continue

        all_leads = deduplicate_leads(all_leads)
        print(f"[Scraper] FINAL: {len(all_leads)} leads unicos (apos dedup)")
        return all_leads[:max_results]
    else:
        leads = _scrape_single_source(
            niche, region, source, max_results,
            block_large_portals, on_progress
        )
        leads = deduplicate_leads(leads)
        print(f"[Scraper] FINAL: {len(leads)} leads unicos (apos dedup)")
        return leads[:max_results]


def get_available_sources():
    """Retorna a lista de fontes de busca disponiveis."""
    return list(SOURCES.keys()) + [ALL_SOURCES_KEY]