"""
Velli Prospect V4 â€” Scraper Engine (Reescrito)
Motor de busca com Google Search (googlesearch-python) como primario,
DDGS como fallback, e validacao rigorosa de relevancia.
"""
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

BLOCKED_DOMAINS = [
    "guiamais.com.br", "apontador.com.br", "facebook.com", "linkedin.com",
    "jusbrasil.com.br", "g1.globo.com", "wikipedia.org", "youtube.com",
    "tripadvisor.com.br", "tripadvisor.com", "mercadolivre.com.br", "shopee.com.br",
    "reclameaqui.com.br", "tiktok.com", "pinterest.com", "sympla.com.br",
    "eventim.com.br", "doctoralia.com.br", "doctoralia.com.pt", "starofservice.pt",
    "fadadodente.pt", "docdental.pt", "olx.com.br", "enjoei.com.br",
    "magazineluiza.com.br", "amazon.com.br", "amazon.com", "yelp.com",
    "glassdoor.com", "glassdoor.com.br", "indeed.com", "indeed.com.br",
    "catho.com.br", "infojobs.com.br", "vagas.com.br", "trampos.co",
    "twitter.com", "x.com", "gov.br", "jus.br", "phhmortgage.com",
    "bing.com", "google.com", "duckduckgo.com",
]

JUNK_INDICATORS = [
    "search results", "resultados da busca", "erro 404", "not found",
    "access denied", "we would like to show you a description",
    "won't allow us", "the site won't allow us", "sign in", "sign up",
    "cadastre-se", "termos de uso", "privacy policy", "cookie policy",
    "page not found", "forbidden", "unauthorized", "server error",
]

SOURCES = {
    "instagram": {
        "query_variations": [
            '"{niche}" "{region}" instagram contato',
            '{niche} {region} instagram whatsapp',
            '{niche} {region} perfil profissional instagram',
        ],
        "skip_domain_filter": True,
    },
    "maps": {
        "query_variations": [
            '"{niche}" "{region}" contato telefone',
            '{niche} {region} escritorio contato whatsapp',
            '{niche} perto de {region} telefone endereco',
        ],
        "skip_domain_filter": False,
    },
    "linkedin": {
        "query_variations": [
            '{niche} {region} site:linkedin.com',
        ],
        "skip_domain_filter": True,
    },
    "maps_insta": {
        "query_variations": [
            '{niche} {region} contato instagram whatsapp',
        ],
        "skip_domain_filter": True,
    },
    "facebook": {
        "query_variations": [
            '{niche} {region} site:facebook.com',
        ],
        "skip_domain_filter": True,
    },
    "Sites Proprios": {
        "query_variations": [
            '"{niche}" "{region}" site:.com.br contato',
            '{niche} {region} escritorio site oficial',
        ],
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
    has_phone = any(re.search(p, text, re.IGNORECASE) for p in phone_patterns)
    emails = re.findall(email_pattern, text, re.IGNORECASE)
    filtered = [e for e in emails if not any(x in e.lower() for x in ["noreply", "no-reply", "example.com", "sentry", "cloudflare"])]
    return has_phone, bool(filtered)


def is_blocked_domain(url, block_large_portals):
    if not block_large_portals:
        return False
    url_lower = url.lower()
    return any(blocked in url_lower for blocked in BLOCKED_DOMAINS)


def _is_junk(title, snippet):
    combined = f"{title} {snippet}".lower()
    return any(junk in combined for junk in JUNK_INDICATORS)


def _is_relevant(title, snippet, niche, region):
    combined = f"{title} {snippet}".lower()
    niche_words = [w for w in niche.lower().split() if len(w) > 2]
    region_words = [w for w in region.lower().split() if len(w) > 2]
    has_niche = any(w in combined for w in niche_words)
    has_region = any(w in combined for w in region_words)
    return has_niche or has_region


def is_valid_business_lead(title, url, snippet, niche="", region=""):
    if not url or not title or len(title.strip()) < 3:
        return False
    if any(b in url.lower() for b in BLOCKED_DOMAINS):
        return False
    if _is_junk(title, snippet):
        return False
    if niche and not _is_relevant(title, snippet, niche, region):
        return False
    return True


def deduplicate_leads(leads):
    seen_links = set()
    seen_names = set()
    unique = []
    for lead in leads:
        link = lead.get("Link", "").lower().strip().rstrip("/")
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


# ============================================================
# MOTORES DE BUSCA
# ============================================================

def _google_search_engine(query, max_results=20):
    if google_search is None:
        return []
    try:
        results = []
        for url in google_search(query, num_results=max_results, lang="pt", region="BR"):
            results.append({"href": url, "title": "", "body": ""})
        if results:
            print(f"[Scraper] Google OK: {len(results)} resultados para '{query[:50]}...'")
        return results
    except Exception as e:
        print(f"[Scraper] Google falhou: {e}")
        return []


def _bing_search(query, max_results=20):
    try:
        import requests, base64, urllib.parse
        from bs4 import BeautifulSoup
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
        }
        url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query) + '&cc=br&setlang=pt-br'
        r = requests.get(url, headers=headers, timeout=6.0)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for item in soup.find_all('li', class_='b_algo'):
            h2 = item.find('h2')
            a = h2.find('a') if h2 else None
            if not a:
                continue
            href = a.get('href', '')
            match = re.search(r'[?&]u=a1([a-zA-Z0-9%+\-=]+)', href)
            if match:
                b64 = match.group(1) + '=' * (-len(match.group(1)) % 4)
                try:
                    href = base64.b64decode(b64).decode('utf-8', errors='ignore')
                except Exception:
                    pass
            snippet_el = item.find('p')
            snippet = snippet_el.text.strip() if snippet_el else a.text.strip()
            results.append({'href': href, 'title': a.text.strip(), 'body': snippet})
        if results:
            print(f"[Scraper] Bing OK: {len(results)} resultados")
        return results
    except Exception as e:
        print(f"[Scraper] Bing falhou: {e}")
        return []


def _ddgs_search(query, max_results=20):
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, region="pt-br"):
                results.append({"href": r.get("href"), "title": r.get("title"), "body": r.get("body")})
        if results:
            print(f"[Scraper] DDGS OK: {len(results)} resultados")
        return results
    except Exception as e:
        print(f"[Scraper] DDGS falhou: {e}")
        return []


def _ddg_lite_search(query, max_results=20):
    import requests
    from bs4 import BeautifulSoup
    import time
    import random
    
    url = 'https://lite.duckduckgo.com/lite/'
    uas = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Mozilla/5.0 (X11; Linux x86_64)',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'
    ]
    
    for attempt in range(3):
        try:
            headers = {'User-Agent': random.choice(uas) + ' AppleWebKit/537.36'}
            r = requests.post(url, data={'q': query}, headers=headers, timeout=10)
            
            if r.status_code == 202 or 'duckduckgo' not in r.text.lower():
                time.sleep(2)
                continue
                
            soup = BeautifulSoup(r.text, 'html.parser')
            results = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if 'http' in href and 'duckduckgo' not in href and not href.startswith('/url?'):
                    title = a.text.strip()
                    if title and len(title) > 3:
                        results.append({'href': href, 'title': title, 'body': ''})
                        if len(results) >= max_results:
                            break
            
            if results:
                print(f"[Scraper] DDG Lite OK (Attempt {attempt+1}): {len(results)} resultados")
                return results
                
        except Exception as e:
            print(f"[Scraper] DDG Lite Attempt {attempt+1} falhou: {e}")
            time.sleep(1)
            
    return []

def _gemini_synthetic_search(query, max_results=20):
    try:
        from google import genai
        import json
        import database as db
        import requests
        
        api_key = db.get_setting("gemini_api_key", "")
        if not api_key: return []
        
        client = genai.Client(api_key=api_key)
        prompt = f"O usuário está buscando: '{query}'. Retorne uma lista de até {max_results} sites reais e existentes que combinem perfeitamente com essa busca no Brasil. Você DEVE retornar APENAS um JSON array. Exemplo: [{{\"title\": \"Nome da Empresa\", \"href\": \"https://www.site.com.br\"}}]"
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt
        )
        
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        
        results = []
        for item in data:
            if isinstance(item, dict) and 'href' in item:
                # Opcional: verificar se o site existe rapidamente
                try:
                    r = requests.head(item['href'], timeout=3)
                    if r.status_code < 400 or r.status_code == 403: # 403 is often valid for bots
                        results.append({"href": item["href"], "title": item.get("title", "Resultado"), "body": ""})
                except:
                    pass
        if results:
            print(f"[Scraper] Gemini Synthetic OK: {len(results)} resultados")
        return results
    except Exception as e:
        print(f"[Scraper] Gemini Synthetic falhou: {e}")
        return []

def _multi_engine_search(query, max_results=20):
    # 1. DDG Lite (Bypassa Cloudflare e funciona bem no Render)
    results = _ddg_lite_search(query, max_results)
    if results:
        return results
        
    # 2. Bing Search (Fallback)
    results = _bing_search(query, max_results)
    if results:
        return results
        
    # 3. Google Search (Fallback)
    results = _google_search_engine(query, max_results)
    if results:
        return results
        
    # 4. DDGS API (Fallback)
    results = _ddgs_search(query, max_results)
    if results:
        return results
        
    # 5. Gemini Synthetic Search (Ultimate Fallback)
    results = _gemini_synthetic_search(query, max_results)
    if results:
        return results
        
    return []


# ============================================================
# ENRIQUECIMENTO
# ============================================================

def _enrich_lead_from_url(url):
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'pt-BR,pt;q=0.9'}
        r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if r.status_code != 200:
            return None, None
        soup = BeautifulSoup(r.text[:10000], 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta = soup.find('meta', attrs={'name': 'description'})
        snippet = meta['content'].strip() if meta and meta.get('content') else ""
        if not snippet:
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 30:
                    snippet = text[:200]
                    break
        return title, snippet
    except Exception:
        return None, None


# ============================================================
# INSTAGRAM VALIDATION
# ============================================================

def is_valid_instagram_profile(url):
    if not url or "instagram.com" not in url.lower():
        return False
    url_clean = url.split("?")[0].split("#")[0].rstrip("/")
    url_lower = url_clean.lower()
    invalid_paths = ["/p/", "/reel/", "/reels/", "/explore/", "/stories/", "/tv/", "/tags/",
        "/popular/", "/directory/", "/accounts/", "/about/", "/legal/", "/help/",
        "/developer/", "/privacy/", "/topics/"]
    if any(p in url_lower for p in invalid_paths):
        return False
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url_clean)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) != 1:
            return False
        return bool(re.match(r"^[a-zA-Z0-9._]{2,30}$", parts[0]))
    except Exception:
        return False


# ============================================================
# SCRAPING PRINCIPAL
# ============================================================

def _scrape_single_source(niche, region, source_key, max_results, block_large_portals, on_progress=None, previously_seen=None):
    leads = []
    source_config = SOURCES.get(source_key, SOURCES["maps"])
    skip_domain = source_config.get("skip_domain_filter", False)
    query_variations = source_config.get("query_variations", ["{niche} {region}"])
    if previously_seen is None:
        previously_seen = set()
    seen_urls_local = set()

    for query_template in query_variations:
        if len(leads) >= max_results:
            break
        query = query_template.format(niche=niche, region=region)
        print(f"[Scraper] Buscando: '{query}' (fonte: {source_key})")
        try:
            fetch_count = min(max_results * 3, 40)
            results = _multi_engine_search(query, fetch_count)
            if not results:
                continue

            for r in results:
                if len(leads) >= max_results:
                    break
                url = r.get("href", "")
                title = r.get("title", "") or ""
                snippet = r.get("body", "") or ""
                if not url:
                    continue

                url_normalized = url.lower().strip().rstrip("/")
                if url_normalized in seen_urls_local or url_normalized in previously_seen:
                    continue
                seen_urls_local.add(url_normalized)

                # Enriquecer se sem titulo (Google Search retorna so URL)
                if not title:
                    try:
                        t, s = _enrich_lead_from_url(url)
                        if t: title = t
                        if s: snippet = s
                    except Exception:
                        pass

                if not title:
                    try:
                        from urllib.parse import urlparse
                        title = urlparse(url).hostname.replace("www.", "").split(".")[0].title()
                    except Exception:
                        title = "Perfil Encontrado"

                if not is_valid_business_lead(title, url, snippet, niche, region):
                    continue

                if not skip_domain and is_blocked_domain(url, block_large_portals):
                    continue

                # Filtro por fonte
                url_lower = url.lower()
                if source_key == "instagram":
                    if not is_valid_instagram_profile(url):
                        continue
                    url = url.split("?")[0].split("#")[0].rstrip("/")
                elif source_key == "linkedin":
                    if "linkedin.com/company/" not in url_lower and "linkedin.com/in/" not in url_lower:
                        continue
                elif source_key == "facebook":
                    if "facebook.com/" not in url_lower:
                        continue

                combined_text = f"{snippet} {title} {url}"
                has_phone, has_email = extract_contact_info(combined_text)

                if title.lower() in ["link to instagram.com", "instagram", ""] and "instagram.com/" in url_lower:
                    try:
                        from urllib.parse import urlparse
                        path_parts = [p for p in urlparse(url).path.split("/") if p]
                        if path_parts:
                            title = path_parts[0].replace("_", " ").replace(".", " ").title()
                    except Exception:
                        pass

                name = _clean_name(title)
                leads.append({
                    "Nome": name, "name": name,
                    "Link": url, "link": url,
                    "Descricao (Bio/Web)": snippet or f"Perfil de {niche} em {region}.",
                    "description": snippet or f"Perfil de {niche} em {region}.",
                    "snippet": snippet or f"Perfil de {niche} em {region}.",
                    "Tem Telefone?": "Sim" if has_phone else "Nao",
                    "Tem E-mail?": "Sim" if has_email else "Nao",
                    "has_phone": has_phone, "has_email": has_email,
                    "_has_contact": has_phone or has_email,
                    "_source": source_key,
                })
                print(f"[Scraper] +Lead: {name[:40]} -> {url[:60]}")
                if on_progress:
                    on_progress(len(leads), max_results, name[:40])
        except Exception as e:
            print(f"[Scraper] Erro ({source_key}): {e}")

    # Fallback
    if not leads:
        fallback_q = f"{niche} {region} contato telefone whatsapp"
        print(f"[Scraper] Fallback: '{fallback_q}'")
        try:
            results = _multi_engine_search(fallback_q, max_results * 2)
            for r in results:
                if len(leads) >= max_results:
                    break
                url = r.get("href", "")
                title = r.get("title", "") or ""
                snippet = r.get("body", "") or ""
                if not url:
                    continue
                if not title:
                    try:
                        t, s = _enrich_lead_from_url(url)
                        if t: title = t
                        if s: snippet = s
                    except Exception:
                        pass
                if not title:
                    try:
                        from urllib.parse import urlparse
                        title = urlparse(url).hostname.replace("www.", "").split(".")[0].title()
                    except Exception:
                        title = "Perfil Encontrado"
                if not is_valid_business_lead(title, url, snippet, niche, region):
                    continue
                if is_blocked_domain(url, block_large_portals):
                    continue
                combined_text = f"{snippet} {title} {url}"
                has_phone, has_email = extract_contact_info(combined_text)
                name = _clean_name(title)
                leads.append({
                    "Nome": name, "name": name, "Link": url, "link": url,
                    "Descricao (Bio/Web)": snippet or f"Perfil de {niche} em {region}.",
                    "description": snippet or f"Perfil de {niche} em {region}.",
                    "Tem Telefone?": "Sim" if has_phone else "Nao",
                    "Tem E-mail?": "Sim" if has_email else "Nao",
                    "has_phone": has_phone, "has_email": has_email,
                    "_has_contact": has_phone or has_email, "_source": source_key
                })
        except Exception as e:
            print(f"[Scraper] Fallback erro: {e}")

    print(f"[Scraper] Fonte '{source_key}' retornou {len(leads)} leads")
    return leads


def _get_previously_scraped_urls():
    try:
        import database
        all_leads = database.get_all_leads()
        seen = set()
        for l in all_leads:
            url = (l.get("link") or "").lower().strip().rstrip("/")
            if url:
                seen.add(url)
        print(f"[Scraper] {len(seen)} URLs anteriores carregadas")
        return seen
    except Exception as e:
        print(f"[Scraper] Erro URLs anteriores: {e}")
        return set()


def scrape_leads(niche, region, sources=None, source=None, max_results=100, block_large_portals=True, on_progress=None, **kwargs):
    sources = sources or source or ALL_SOURCES_KEY
    # To guarantee we reach the EXACT amount after AI discards, we fetch 5x the requested amount (no hard cap)
    target_pool = max_results * 5

    print(f"\n{'='*60}")
    print(f"[Scraper V4] nicho='{niche}', regiao='{region}', fontes='{sources}', meta_bruta={target_pool} para obter {max_results} liquidos")
    print(f"{'='*60}")

    previously_seen = _get_previously_scraped_urls()

    if isinstance(sources, str):
        source_keys = list(SOURCES.keys()) if sources == ALL_SOURCES_KEY else [sources]
    else:
        source_keys = sources

    if not source_keys:
        return []

    per_source = max(target_pool // len(source_keys), 15)

    all_leads = []
    executor = ThreadPoolExecutor(max_workers=min(len(source_keys), 4))
    try:
        future_to_source = {
            executor.submit(_scrape_single_source, niche, region, sk, per_source, block_large_portals, on_progress, previously_seen): sk
            for sk in source_keys
        }
        for future in as_completed(future_to_source, timeout=45):
            sk = future_to_source[future]
            try:
                batch = future.result()
                all_leads.extend(batch)
            except Exception as e:
                print(f"[Scraper] Fonte '{sk}' falhou: {e}")
    except Exception as e:
        print(f"[Scraper] Erro geral: {e}")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    all_leads = deduplicate_leads(all_leads)
    print(f"[Scraper V4] FINAL: {len(all_leads)} leads unicos")
    return all_leads[:target_pool]
