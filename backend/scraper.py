"""
Velli Prospect V3 — Scraper Engine (Revisado v3)
Motor de busca robusto com fallback para servidores cloud.
Usa DuckDuckGo Search (DDGS) com proxy automatico, retry e tratamento de erro visivel.
"""
import re
import time
import traceback

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

BLOCKED_DOMAINS = [
    "guiamais.com.br", "apontador.com.br", "facebook.com", "linkedin.com",
    "jusbrasil.com.br", "g1.globo.com", "wikipedia.org", "youtube.com",
    "tripadvisor.com.br", "mercadolivre.com.br", "shopee.com.br", "reclameaqui.com.br",
    "tiktok.com", "pinterest.com", "sympla.com.br", "eventim.com.br", "doctoralia.com.br",
    "olx.com.br", "enjoei.com.br", "magazineluiza.com.br", "amazon.com.br",
    "yelp.com", "glassdoor.com", "glassdoor.com.br", "indeed.com", "indeed.com.br",
    "catho.com.br", "infojobs.com.br", "vagas.com.br", "trampos.co",
    "twitter.com", "x.com", "gov.br",
]

SOURCES = {
    "instagram": {
        "query_template": "{niche} {region} instagram perfil contato",
        "skip_domain_filter": True,
    },
    "maps": {
        "query_template": "{niche} {region} contato telefone",
        "skip_domain_filter": False,
    },
    "linkedin": {
        "query_template": "{niche} {region} linkedin perfil empresa contato",
        "skip_domain_filter": True,
    },
    "maps_insta": {
        "query_template": "{niche} {region} contato instagram whatsapp",
        "skip_domain_filter": True,
    },
    "facebook": {
        "query_template": "{niche} {region} facebook pagina contato",
        "skip_domain_filter": True,
    },
    "Sites Proprios": {
        "query_template": "{niche} {region} contato site empresa",
        "skip_domain_filter": False,
    },
}

ALL_SOURCES_KEY = "Todas as Fontes"

def extract_contact_info(text):
    phone_patterns = [
        r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)(?:9\s?\d{4})[\s.\-]?\d{4}",
        r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)(?:\d{4})[\s.\-]?\d{4}",
        r"(?:whatsapp|wpp|zap)[\s:]*(?:\+?55\s?)?\(?\d{2}\)?\s?\d{4,5}[\-\s.]?\d{4}",
    ]
    email_pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"

    has_phone = False
    for pattern in phone_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            has_phone = True
            break

    emails = re.findall(email_pattern, text, re.IGNORECASE)
    filtered_emails = [e for e in emails if not any(
        x in e.lower() for x in ["noreply", "no-reply", "example.com", "sentry", "cloudflare"]
    )]
    has_email = bool(filtered_emails)

    return has_phone, has_email

def is_blocked_domain(url, block_large_portals):
    if not block_large_portals:
        return False
    url_lower = url.lower()
    return any(blocked in url_lower for blocked in BLOCKED_DOMAINS)

def deduplicate_leads(leads):
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
    for sep in [" - ", " | ", " \u2014 ", " \u00b7 ", " :: "]:
        if sep in title:
            title = title.split(sep)[0]
    return title.strip() or "Perfil Encontrado"

def _ddgs_search_with_retry(query, max_results, max_retries=2):
    last_error = None

    for attempt in range(max_retries):
        try:
            ddgs = DDGS()
            # Strict limit to 30 results for fast response
            results = list(ddgs.text(query, backend="lite", max_results=min(max_results, 30)))
            if results:
                print(f"[Scraper] Busca OK: {len(results)} resultados (tentativa {attempt+1})")
                return results
            else:
                continue
        except Exception as e:
            last_error = e
            time.sleep(0.5)

    print(f"[Scraper] DDGS FALHOU apos {max_retries} tentativas. Tentando Google Search fallback...")
    
    if google_search is not None:
        try:
            results = []
            for url in google_search(query, num_results=max_results, lang="pt"):
                results.append({"href": url, "title": "Google Result", "body": "Scraped via Google Search Fallback"})
            if results:
                print(f"[Scraper] Google Fallback OK: {len(results)} resultados")
                return results
        except Exception as ge:
            print(f"[Scraper] Google Fallback falhou: {ge}")
            
    return []

def _scrape_single_source(niche, region, source_key, max_results, block_large_portals, on_progress=None):
    leads = []
    source_config = SOURCES.get(source_key, SOURCES["maps"])
    query = source_config["query_template"].format(niche=niche, region=region)
    if source_key == "fallback":
        query = f"{niche} {region} contato site:.com.br"
        skip_domain = False
    else:
        skip_domain = source_config["skip_domain_filter"]

    print(f"[Scraper] Buscando: '{query}' (fonte: {source_key}, max: {max_results})")

    try:
        # Cap fetch_count at 40 to avoid DDGS rate limits and long hangs
        fetch_count = min(max_results * 2, 40)
        results = _ddgs_search_with_retry(query, fetch_count)

        if not results:
            print(f"[Scraper] Nenhum resultado retornado para fonte '{source_key}'")
            return leads

        print(f"[Scraper] {len(results)} resultados brutos recebidos de '{source_key}'")

        for r in results:
            url = r.get("href", "")
            title = r.get("title", "")
            snippet = r.get("body", "")

            if not skip_domain and is_blocked_domain(url, block_large_portals):
                continue

            # --- FILTRO ESPECIFICO POR FONTE ---
            url_lower = url.lower()
            if source_key == "instagram":
                # Must be a direct profile link, not a post/reel
                if "instagram.com" not in url_lower:
                    continue
                if any(x in url_lower for x in ["/p/", "/reel/", "/reels/", "/explore/", "/stories/", "/tv/", "/tags/"]):
                    continue
                # If there are query parameters like ?igshid=... remove them for cleanliness
                url = url.split("?")[0]
            
            elif source_key == "linkedin":
                if "linkedin.com/company/" not in url_lower and "linkedin.com/in/" not in url_lower:
                    continue
            
            elif source_key == "facebook":
                if "facebook.com/" not in url_lower:
                    continue
                    
            elif source_key == "maps_insta":
                if "instagram.com" in url_lower and any(x in url_lower for x in ["/p/", "/reel/", "/reels/", "/explore/"]):
                    continue

            combined_text = f"{snippet} {title} {url}"
            has_phone, has_email = extract_contact_info(combined_text)

            name = _clean_name(title)

            lead = {
                "Nome": name,
                "Link": url,
                "Descricao (Bio/Web)": snippet,
                "Tem Telefone?": "Sim" if has_phone else "Nao",
                "Tem E-mail?": "Sim" if has_email else "Nao",
                "_has_contact": has_phone or has_email,
                "_source": source_key,
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

from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape_leads(niche, region, sources, max_results=100, block_large_portals=True, on_progress=None):
    target_pool = min(max_results * 2, 100)
    
    print(f"\n{'='*60}")
    print(f"[Scraper] INICIO PARALELO TURBO: nicho='{niche}', regiao='{region}', fontes='{sources}', meta_pool={target_pool}")
    print(f"{'='*60}")

    all_leads = []
    
    if isinstance(sources, str):
        if sources == ALL_SOURCES_KEY:
            source_keys = list(SOURCES.keys())
        else:
            source_keys = [sources]
    else:
        source_keys = sources

    if not source_keys:
        return []

    per_source = max(target_pool // len(source_keys), 15)

    # Parallel scraping across sources with ThreadPoolExecutor without blocking shutdown
    executor = ThreadPoolExecutor(max_workers=min(len(source_keys), 6))
    try:
        future_to_source = {
            executor.submit(_scrape_single_source, niche, region, src_key, per_source, block_large_portals, on_progress): src_key
            for src_key in source_keys
        }
        
        for future in as_completed(future_to_source, timeout=12):
            src_key = future_to_source[future]
            try:
                batch = future.result(timeout=2)
                all_leads.extend(batch)
                print(f"[Scraper] Fonte '{src_key}' retornou {len(batch)} leads")
            except Exception as e:
                print(f"[Scraper] Fonte '{src_key}' falhou ou timeout: {e}")
    except Exception as e:
        print(f"[Scraper] Timeout/Erro geral na raspagem paralela: {e}")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    all_leads = deduplicate_leads(all_leads)
    print(f"[Scraper] FINAL: {len(all_leads)} leads unicos (apos dedup)")
    return all_leads[:target_pool]

def get_available_sources():
    return list(SOURCES.keys()) + [ALL_SOURCES_KEY]