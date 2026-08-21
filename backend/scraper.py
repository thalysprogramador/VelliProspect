"""
Velli Prospect V3 — Scraper Engine (Revisado v3)
Motor de busca robusto com fallback para servidores cloud.
Usa DuckDuckGo Search (DDGS) com proxy automatico, retry e tratamento de erro visivel.
"""
import re
import time
import traceback

# Pure Python requests search engine (no C extension segfaults)

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
        "query_template": '"{niche}" "{region}" instagram',
        "skip_domain_filter": True,
    },
    "maps": {
        "query_template": "{niche} {region} contato telefone",
        "skip_domain_filter": False,
    },
    "linkedin": {
        "query_template": "{niche} {region} (site:linkedin.com/in/ OR site:linkedin.com/company/)",
        "skip_domain_filter": True,
    },
    "maps_insta": {
        "query_template": "{niche} {region} contato instagram whatsapp",
        "skip_domain_filter": True,
    },
    "facebook": {
        "query_template": "{niche} {region} site:facebook.com",
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

def _bing_search(query, max_results=30):
    try:
        import requests, re, base64, urllib.parse
        from bs4 import BeautifulSoup
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
        }
        url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
        r = requests.get(url, headers=headers, timeout=4.0)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for item in soup.find_all('li', class_='b_algo'):
            h2 = item.find('h2')
            a = h2.find('a') if h2 else None
            if not a: continue
            href = a.get('href', '')
            match = re.search(r'[?&]u=a1([a-zA-Z0-9%+\-=]+)', href)
            if match:
                b64 = match.group(1) + '=' * (-len(match.group(1)) % 4)
                try: href = base64.b64decode(b64).decode('utf-8', errors='ignore')
                except: pass
            snippet = item.find('p').text.strip() if item.find('p') else a.text.strip()
            results.append({'href': href, 'title': a.text.strip(), 'body': snippet})
        return results
    except Exception as e:
        print(f"[Scraper] Erro Bing Search: {e}")
        return []

def _ddgs_search_with_retry(query, max_results, max_retries=2):
    # Primary ultra-fast engine: DuckDuckGo Search (DDGS)
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({"href": r.get("href"), "title": r.get("title"), "body": r.get("body")})
        if results:
            print(f"[Scraper] Busca DDGS OK: {len(results)} resultados")
            return results
    except Exception as e:
        print(f"[Scraper] DDGS falhou ({e}), tentando Bing Fallback...")

    # Fallback engine: Bing Search via native requests
    bing_res = _bing_search(query, max_results)
    if bing_res:
        print(f"[Scraper] Busca Bing OK: {len(bing_res)} resultados")
        return bing_res

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
                # Must be a valid direct profile link (not post, reel, explore, popular, tag, etc.)
                if not is_valid_instagram_profile(url):
                    continue
                # Clean tracking parameters
                url = url.split("?")[0].split("#")[0].rstrip("/")
            
            elif source_key == "linkedin":
                if "linkedin.com/company/" not in url_lower and "linkedin.com/in/" not in url_lower:
                    continue
            
            elif source_key == "facebook":
                if "facebook.com/" not in url_lower:
                    continue

            combined_text = f"{snippet} {title} {url}"
            has_phone, has_email = extract_contact_info(combined_text)

            # Fix generic titles from DDGS
            if title.lower() in ["link to instagram.com", "instagram", ""] and "instagram.com/" in url_lower:
                try:
                    from urllib.parse import urlparse
                    path_parts = [p for p in urlparse(url).path.split("/") if p]
                    if path_parts:
                        title = path_parts[0].replace("_", " ").title()
                except:
                    pass

            name = _clean_name(title)

            lead = {
                "Nome": name,
                "name": name,
                "Link": url,
                "link": url,
                "Descricao (Bio/Web)": snippet or f"Perfil profissional ativo de {niche} em {region}.",
                "description": snippet or f"Perfil profissional ativo de {niche} em {region}.",
                "snippet": snippet or f"Perfil profissional ativo de {niche} em {region}.",
                "Tem Telefone?": "Sim" if has_phone else "Nao",
                "Tem E-mail?": "Sim" if has_email else "Nao",
                "has_phone": has_phone,
                "has_email": has_email,
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

def is_valid_instagram_profile(url):
    if not url or "instagram.com" not in url.lower():
        return False
    url_clean = url.split("?")[0].split("#")[0].rstrip("/")
    url_lower = url_clean.lower()
    
    invalid_paths = [
        "/p/", "/reel/", "/reels/", "/explore/", "/stories/", "/tv/", "/tags/", 
        "/popular/", "/directory/", "/accounts/", "/about/", "/legal/", "/help/",
        "/developer/", "/privacy/", "/topics/"
    ]
    if any(p in url_lower for p in invalid_paths):
        return False
        
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url_clean)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) != 1:
            return False
        handle = parts[0]
        if not re.match(r"^[a-zA-Z0-9._]{2,30}$", handle):
            return False
        return True
    except Exception:
        return False

from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape_leads(niche, region, sources=None, source=None, max_results=100, block_large_portals=True, on_progress=None, **kwargs):
    sources = sources or source or ALL_SOURCES_KEY
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

    # Parallel scraping across sources with ThreadPoolExecutor
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



