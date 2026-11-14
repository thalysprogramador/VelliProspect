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
    "bing.com", "google.com", "duckduckgo.com", "econodata.com.br",
    "guiapj.com.br", "cnpj.biz", "casadosdados.com.br", "solutudo.com.br",
    "cylex.com.br", "polomap.com", "inddex.com.br", "cnpja.com", "codycrossanswers.com",
]

JUNK_INDICATORS = [
    "search results", "resultados da busca", "erro 404", "not found",
    "access denied", "we would like to show you a description",
    "won't allow us", "the site won't allow us", "sign in", "sign up",
    "cadastre-se", "termos de uso", "privacy policy", "cookie policy",
    "page not found", "forbidden", "unauthorized", "server error",
    "as 10 melhores", "os 10 melhores", "os 20 ", "as 20 ", "melhores clinicas", "melhores escritorios",
    "software para", "software de gestao", "sistema de gestao", "sistema para",
    "tudo sobre", "guia das profissoes", "como montar", "como abrir",
    "maiores empresas de", "consulta cnpj",
]

SOURCES = {
    "instagram": {
        "query_variations": [
            'site:instagram.com {niche} {region}',
            '{niche} {region} instagram.com',
            'site:instagram.com clinica {niche} {region}',
            'site:instagram.com {niche} em {region}',
            'site:instagram.com consultorio {niche} {region}',
            'site:instagram.com especialista {niche} {region}',
            'site:instagram.com {niche} {region} whatsapp',
        ],
        "skip_domain_filter": True,
    },
    "maps": {
        "query_variations": [
            '{niche} em {region} telefone whatsapp',
            '{niche} {region} site:.com.br contato',
            '"{niche}" "{region}" contato telefone',
            '{niche} {region} atendimento whatsapp',
            'clinica consultorio escritorio {niche} {region} telefone',
            'empresa {niche} {region} contato telefone',
        ],
        "skip_domain_filter": False,
    },
    "linkedin": {
        "query_variations": [
            '{niche} {region} site:linkedin.com/company',
            '{niche} {region} site:linkedin.com/in',
            'empresa {niche} {region} linkedin',
            'fundador {niche} {region} linkedin',
        ],
        "skip_domain_filter": True,
    },
    "maps_insta": {
        "query_variations": [
            '{niche} {region} contato instagram whatsapp',
            '{niche} {region} instagram telefone',
            '{niche} {region} perfil instagram',
        ],
        "skip_domain_filter": True,
    },
    "facebook": {
        "query_variations": [
            '{niche} {region} site:facebook.com',
            '{niche} {region} pagina facebook contato',
        ],
        "skip_domain_filter": True,
    },
    "Sites Proprios": {
        "query_variations": [
            '"{niche}" "{region}" site:.com.br contato',
            '{niche} {region} escritorio site oficial',
            '{niche} {region} empresa contato telefone',
            '"{niche}" em {region} fale conosco',
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
    combined = _normalize_text(f"{title} {snippet}")
    return any(junk in combined for junk in JUNK_INDICATORS)


def _normalize_text(s):
    if not s:
        return ""
    import unicodedata
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode("ascii")


def _is_relevant(title, snippet, niche, region):
    combined = _normalize_text(f"{title} {snippet}")
    niche_words = []
    for w in _normalize_text(niche).split():
        if len(w) > 2:
            niche_words.append(w)
            if len(w) > 4 and w.endswith("s"):
                niche_words.append(w[:-1])
    region_words = [w for w in _normalize_text(region).split() if len(w) > 2]
    has_niche = any(w in combined for w in niche_words) if niche_words else True
    has_region = any(w in combined for w in region_words) if region_words else True
    return has_niche and has_region


def is_valid_business_lead(title, url, snippet, niche="", region="", skip_domain=False):
    if not url or not title or len(title.strip()) < 3:
        return False
    if not skip_domain and any(b in url.lower() for b in BLOCKED_DOMAINS):
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
    if not title:
        return "Perfil Encontrado"
    for suffix in [
        " \u2022 Instagram profile",
        " \u2022 Instagram photos and videos",
        " \u2022 Instagram photo",
        " \u2022 Instagram reel",
        " \u2022 Fotos e v\u00eddeos do Instagram",
        " | Instagram",
        " | LinkedIn",
        " | Facebook",
    ]:
        if suffix.lower() in title.lower():
            idx = title.lower().find(suffix.lower())
            title = title[:idx]
    for sep in [" - ", " | ", " \u2014 ", " \u00b7 ", " :: ", " \u2022 "]:
        if sep in title:
            title = title.split(sep)[0]
    return title.strip() or "Perfil Encontrado"


def _safe_str(s):
    if not s:
        return ""
    try:
        return str(s).encode("ascii", errors="replace").decode("ascii")
    except Exception:
        return ""


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
    results = []
    seen_hrefs = set()
    try:
        from ddgs.engines.yandex import Yandex
        eng = Yandex()
        # Faz ate 3 chamadas rapidas em page=1 (cada searchid traz ~6-12 resultados reais)
        for attempt in range(3):
            try:
                raw_items = eng.search(query, region="br-pt", safesearch="moderate", timelimit=None, page=1)
                if raw_items:
                    for item in raw_items:
                        href = getattr(item, "href", "") or ""
                        if not href or href in seen_hrefs:
                            continue
                        seen_hrefs.add(href)
                        results.append({
                            "href": href,
                            "title": getattr(item, "title", "") or "",
                            "body": getattr(item, "body", "") or "",
                        })
                if len(results) >= max_results or (results and attempt >= 1):
                    break
            except Exception:
                pass
        if results:
            print(f"[Scraper] Yandex Direct OK: {len(results)} resultados para '{_safe_str(query)[:50]}'")
            return results[:max_results]
    except Exception as e:
        print(f"[Scraper] Yandex Direct erro: {e}")
    return results


def _generate_smart_queries(niche, region, source_key, criteria=""):
    try:
        from google import genai
        import database as db
        import json
        api_key = db.get_setting("gemini_api_key", db.DEFAULT_GEMINI_KEY)
        if not api_key:
            return []
        client = genai.Client(api_key=api_key)
        sk_lower = str(source_key).lower()
        prefix_hint = "Inclua 'site:instagram.com ' no inicio de cada termo." if "instagram" in sk_lower else ""
        prompt = f"""Gere 6 termos de busca curtos e altamente eficazes para encontrar no DuckDuckGo/Google empresas e profissionais reais no Brasil.
{prefix_hint}
Use variacoes inteligentes de especialidades, sinonimos do nicho e termos locais da cidade/regiao.
Nicho: {niche}
Regiao: {region}
Fonte: {source_key}
Criterios/Segmentacao desejada pelo usuario: {criteria or 'Negocios e profissionais reais ativos na regiao'}
Retorne APENAS um JSON array de strings com as buscas. Exemplo: ["termo 1", "termo 2"]"""

        import ai_evaluator
        res = ai_evaluator._call_gemini_with_retry(client, prompt, model="gemini-3.5-flash-lite")
        text = res.text.replace("```json", "").replace("```", "").strip()
        queries = json.loads(text)
        if isinstance(queries, list):
            valid = [str(q).strip() for q in queries if q and isinstance(q, str)]
            print(f"[Scraper] Queries inteligentes com IA geradas ({len(valid)}): {valid[:3]}")
            return valid
    except Exception as e:
        print(f"[Scraper] Erro ao gerar queries inteligentes com IA: {e}")
    return []


def _multi_engine_search(query, max_results=20, source_key="maps"):
    # 1. DDGS Search (backend="yandex") - Imune a bloqueio/honeypot de IPs de datacenter AWS/Render
    try:
        results = _ddgs_search(query, max_results)
        if results:
            return results
    except Exception:
        pass

    # 2. Google Search (fallback)
    try:
        results = _google_search_engine(query, max_results)
        if results:
            return results
    except Exception:
        pass

    return []


# ============================================================
# VERIFICACAO REAL E ENRIQUECIMENTO DE URLS (AO VIVO)
# ============================================================

def _enrich_lead_from_url(url):
    """Extrai titulo e descricao reais de uma URL e valida se ela realmente existe."""
    if not url:
        return None, None
    url_lower = url.lower()
    try:
        import requests
        from bs4 import BeautifulSoup
        is_social = "instagram.com" in url_lower or "facebook.com" in url_lower
        headers = {
            'User-Agent': 'TelegramBot (like TwitterBot)' if is_social else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
        }
        r = requests.get(url, headers=headers, timeout=4.5, allow_redirects=True)
        if r.status_code >= 400:
            return None, None
        soup = BeautifulSoup(r.text[:35000], 'html.parser')

        def _meta(prop=None, name=None):
            tag = soup.find('meta', property=prop) if prop else soup.find('meta', attrs={'name': name})
            return tag.get('content', '').strip() if tag and tag.get('content') else ""

        og_title = _meta(prop='og:title') or _meta(name='twitter:title')
        og_desc = _meta(prop='og:description') or _meta(name='twitter:description') or _meta(name='description')

        if is_social:
            # Perfis inexistentes no Instagram retornam HTML sem og:title e sem twitter:title
            if not og_title or og_title.strip().lower() in ["instagram", "login \u2022 instagram", "entrar \u2022 instagram", "facebook", "log in or sign up to view"]:
                return None, None
            return og_title, og_desc

        title = og_title or (soup.title.string.strip() if soup.title and soup.title.string else "")
        snippet = og_desc
        if not snippet:
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 30:
                    snippet = text[:240]
                    break
        return title, snippet
    except Exception:
        return None, None


def _format_ig_handle_title(handle):
    """Formata um @handle real do Instagram em um titulo legivel caso o IP do servidor sofra rate-limit no OpenGraph."""
    h = handle.replace("_", " ").replace(".", " ").strip()
    prefixes = [
        ("clinica", "Clínica "),
        ("consultorio", "Consultório "),
        ("escritorio", "Escritório "),
        ("instituto", "Instituto "),
        ("dra", "Dra. "),
        ("dr", "Dr. "),
        ("odonto", "Odonto "),
        ("studio", "Studio "),
        ("espaco", "Espaço "),
    ]
    h_lower = h.lower()
    for p_raw, p_nice in prefixes:
        if h_lower.startswith(p_raw) and len(h_lower) > len(p_raw) and h_lower[len(p_raw)] != " ":
            h = p_nice + h[len(p_raw):]
            break
    readable = " ".join(w.capitalize() if not w.endswith(".") else w for w in h.split())
    return f"{readable} (@{handle})"


def _verify_and_build_lead(raw_item, source_key, niche, region, block_large_portals=True, skip_domain=False):
    """
    Verifica se a URL retornada pela busca real existe,
    converte posts/reels do Instagram para o perfil comercial real (@handle) quando possivel,
    e retorna o dicionario de lead validado ou None se invalido/inexistente.
    """
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse

    url = (raw_item.get("href") or "").strip()
    title = (raw_item.get("title") or "").strip()
    snippet = (raw_item.get("body") or "").strip()
    if not url or not url.startswith("http"):
        return None

    url_lower = url.lower()

    # Caso 1: URL do Instagram (validacao real via DDGS + OpenGraph TelegramBot)
    if "instagram.com" in url_lower:
        blocked_ig = [
            "/explore/", "/stories/", "/tags/", "/popular/", "/directory/",
            "/accounts/", "/about/", "/legal/", "/help/", "/developer/",
            "/privacy/", "/topics/", "/challenge/", "/login/"
        ]
        if any(b in url_lower for b in blocked_ig):
            return None

        ddgs_title = title.split("...")[0].strip() if "..." in title else title
        has_ddgs_meta = bool(
            ddgs_title
            and "link to instagram" not in ddgs_title.lower()
            and ddgs_title.lower().strip() != "instagram"
            and snippet
            and "the site owner hides" not in snippet.lower()
        )

        best_title = ""
        og_desc = ""
        og_url = ""
        try:
            headers = {
                'User-Agent': 'TelegramBot (like TwitterBot)',
                'Accept-Language': 'pt-BR,pt;q=0.9'
            }
            r = requests.get(url, headers=headers, timeout=2.5, allow_redirects=True)
            if r.status_code < 400:
                soup = BeautifulSoup(r.text[:35000], 'html.parser')

                def _meta(prop=None, name=None):
                    tag = soup.find('meta', property=prop) if prop else soup.find('meta', attrs={'name': name})
                    return tag.get('content', '').strip() if tag and tag.get('content') else ""

                og_title = _meta(prop='og:title')
                tw_title = _meta(name='twitter:title')
                og_desc = _meta(prop='og:description') or _meta(name='twitter:description')
                og_url = _meta(prop='og:url')
                candidate_t = tw_title or og_title
                if candidate_t and candidate_t.lower().strip() not in ["instagram", "login \u2022 instagram", "entrar \u2022 instagram"]:
                    best_title = candidate_t
        except Exception:
            pass

        # Extrair @handle se for post (/p/, /reel/, /tv/) ou confirmar handle do perfil direto
        handle = None
        m_url = re.search(r"instagram\.com/([a-zA-Z0-9._]{2,30})/(?:p|reel|reels|tv)/", og_url or url, re.IGNORECASE)
        if m_url:
            handle = m_url.group(1)
        if not handle:
            m_title = re.search(r"\(@([a-zA-Z0-9._]{2,30})\)", f"{best_title} {ddgs_title} {og_desc} {snippet}")
            if m_title:
                handle = m_title.group(1)
        if not handle:
            m_desc = re.search(r"-\s*([a-zA-Z0-9._]{2,30})\s+on\s+", f"{og_desc} {snippet}")
            if m_desc:
                handle = m_desc.group(1)
        if not handle:
            parts = [p for p in urlparse(url.split("?")[0].split("#")[0]).path.split("/") if p]
            if len(parts) == 1 and re.match(r"^[a-zA-Z0-9._]{2,30}$", parts[0]):
                handle = parts[0]

        reserved_handles = {
            "p", "reel", "reels", "explore", "stories", "tv", "tags",
            "popular", "directory", "accounts", "about", "legal", "help",
            "developer", "privacy", "topics", "instagram"
        }
        if not handle or handle.lower() in reserved_handles:
            return None

        profile_url = f"https://www.instagram.com/{handle}"
        if not is_valid_instagram_profile(profile_url):
            return None

        if not best_title:
            if has_ddgs_meta:
                best_title = ddgs_title
                og_desc = snippet
            else:
                # Se o Instagram nao retornou og:title/twitter:title ao vivo, o perfil foi desativado ou nao existe
                return None

        clean_desc_parts = []
        if og_desc:
            clean_desc_parts.append(og_desc)
        if snippet and "the site owner hides" not in snippet.lower() and snippet not in (og_desc or ""):
            clean_desc_parts.append(snippet)

        final_snippet = " | ".join(clean_desc_parts).strip()
        if not final_snippet or "the site owner hides" in final_snippet.lower():
            final_snippet = f"Perfil comercial real verificado no Instagram (@{handle}) — {niche} em {region}."
        elif _normalize_text(region) not in _normalize_text(f"{best_title} {final_snippet}"):
            final_snippet = f"{final_snippet} | Atuação: {niche} ({region})"

        title = best_title
        url = profile_url
        snippet = final_snippet[:500]

    # Caso 2: LinkedIn
    elif "linkedin.com" in url_lower:
        if "linkedin.com/company/" not in url_lower and "linkedin.com/in/" not in url_lower:
            return None
        if not title or "link to linkedin" in title.lower():
            return None
        if "the site owner hides" in snippet.lower():
            snippet = f"{title} - Perfil profissional no LinkedIn ({niche} em {region})."
        url = url.split("?")[0].split("#")[0].rstrip("/")

    # Caso 3: Facebook
    elif "facebook.com" in url_lower:
        blocked_fb = ["/posts/", "/photos/", "/videos/", "/groups/", "/events/", "/watch/", "/marketplace/", "/login/", "/help/", "/sharer"]
        if any(b in url_lower for b in blocked_fb):
            return None
        t_fb, s_fb = _enrich_lead_from_url(url)
        if t_fb:
            title = t_fb
        if s_fb:
            snippet = s_fb
        if not title or title.lower().strip() in ["facebook", "log in or sign up to view", "entrar no facebook"]:
            return None
        url = url.split("?")[0].split("#")[0].rstrip("/")

    # Caso 4: Sites Proprios / Google Maps / Negocios Locais
    else:
        if not skip_domain and is_blocked_domain(url, block_large_portals):
            return None
        # Verificar se o site realmente abre e existe (status < 400)
        t_web, s_web = _enrich_lead_from_url(url)
        if t_web is None and s_web is None:
            return None
        if not title or "link to " in title.lower():
            title = t_web or ""
        if not snippet or "the site owner hides" in snippet.lower() or len(snippet) < 25:
            snippet = s_web or snippet
        if not is_valid_business_lead(title, url, snippet, niche, region, skip_domain=skip_domain):
            return None

    if _is_junk(title, snippet):
        return None

    combined_text = f"{snippet} {title} {url}"
    has_phone, has_email = extract_contact_info(combined_text)
    name = _clean_name(title)
    if not name or len(name) < 2 or name.lower() in ["instagram", "facebook", "linkedin", "perfil encontrado"]:
        return None

    return {
        "Nome": name,
        "name": name,
        "Link": url,
        "link": url,
        "Descricao (Bio/Web)": snippet or f"Perfil comercial verificado de {niche} em {region}.",
        "description": snippet or f"Perfil comercial verificado de {niche} em {region}.",
        "snippet": snippet or f"Perfil comercial verificado de {niche} em {region}.",
        "Tem Telefone?": "Sim" if has_phone else "Nao",
        "Tem E-mail?": "Sim" if has_email else "Nao",
        "has_phone": has_phone,
        "has_email": has_email,
        "_has_contact": has_phone or has_email,
        "_source": source_key,
    }


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
# SCRAPING PRINCIPAL (100% REAIS E VERIFICADOS AO VIVO)
# ============================================================

def _process_raw_results_parallel(raw_results, source_key, niche, region, block_large_portals, skip_domain, seen_urls_local, previously_seen, max_needed):
    """Verifica e enriquece em paralelo os resultados brutos de busca, retornando apenas perfis/sites reais e ativos."""
    candidates = []
    for r in raw_results:
        url = (r.get("href") or "").strip()
        if not url or not url.startswith("http"):
            continue
        url_norm = url.split("?")[0].split("#")[0].lower().strip().rstrip("/")
        if url_norm in seen_urls_local or url_norm in previously_seen:
            continue
        seen_urls_local.add(url_norm)
        candidates.append(r)
        if len(candidates) >= max(max_needed * 3, 24):
            break

    if not candidates:
        return []

    verified_leads = []
    with ThreadPoolExecutor(max_workers=min(len(candidates), 10)) as pool:
        futures = [
            pool.submit(_verify_and_build_lead, r, source_key, niche, region, block_large_portals, skip_domain)
            for r in candidates
        ]
        for fut in as_completed(futures, timeout=25):
            try:
                lead = fut.result()
                if not lead:
                    continue
                final_url_norm = lead["Link"].lower().strip().rstrip("/")
                if final_url_norm in previously_seen:
                    continue
                # Evitar duplicatas quando 2 posts diferentes convertem para o mesmo @perfil
                if any(l["Link"].lower().strip().rstrip("/") == final_url_norm for l in verified_leads):
                    continue
                seen_urls_local.add(final_url_norm)
                verified_leads.append(lead)
            except Exception:
                pass
    return verified_leads


def _scrape_single_source(niche, region, source_key, max_results, block_large_portals, on_progress=None, previously_seen=None, criteria=""):
    leads = []
    sk_norm = str(source_key).lower().strip()
    if sk_norm in SOURCES:
        source_key = sk_norm
    source_config = SOURCES.get(source_key, SOURCES["maps"])
    skip_domain = source_config.get("skip_domain_filter", False)
    base_queries = list(source_config.get("query_variations", ["{niche} {region}"]))

    formatted_base = [q.format(niche=niche, region=region) for q in base_queries]
    all_query_templates = list(formatted_base)

    if criteria and criteria.strip():
        crit_short = criteria.strip()[:35]
        if source_key == "instagram":
            all_query_templates.insert(2, f"{niche} {region} {crit_short} instagram.com")
            all_query_templates.insert(3, f"site:instagram.com {niche} {region} {crit_short}")
        else:
            all_query_templates.insert(0, f"{niche} {region} {crit_short} telefone whatsapp")

    all_query_templates = list(dict.fromkeys(all_query_templates))[:6]

    if previously_seen is None:
        previously_seen = set()
    seen_urls_local = set()

    empty_streak = 0
    for query in all_query_templates:
        if len(leads) >= max_results:
            break
        if empty_streak >= 3:
            break
        before_count = len(leads)
        print(f"[Scraper] Buscando: '{_safe_str(query)}' (fonte: {source_key})")
        try:
            fetch_count = min(max(max_results * 3, 25), 40)
            results = _multi_engine_search(query, fetch_count, source_key=source_key)
            if not results:
                empty_streak += 1
                continue

            needed_now = max_results - len(leads)
            verified_batch = _process_raw_results_parallel(
                results, source_key, niche, region, block_large_portals, skip_domain,
                seen_urls_local, previously_seen, needed_now
            )
            for lead in verified_batch:
                if len(leads) >= max_results:
                    break
                if any(l["Link"].lower().strip().rstrip("/") == lead["Link"].lower().strip().rstrip("/") for l in leads):
                    continue
                leads.append(lead)
                print(f"[Scraper] +Lead Real Verificado: {_safe_str(lead['Nome'])[:40]} -> {_safe_str(lead['Link'])[:60]}")
                if on_progress:
                    on_progress(len(leads), max_results, _safe_str(lead['Nome'])[:40])

            if len(leads) == before_count:
                empty_streak += 1
            else:
                empty_streak = 0
        except Exception as e:
            print(f"[Scraper] Erro ({source_key}): {_safe_str(str(e))}")
            empty_streak += 1

    # Se ainda faltar leads, gerar variacoes inteligentes de busca com IA e validar todas ao vivo
    if len(leads) < max_results:
        needed = max_results - len(leads)
        print(f"[Scraper] Expandindo buscas reais para completar {needed} leads faltantes...")
        smart_queries = _generate_smart_queries(niche, region, source_key, criteria)
        if not smart_queries:
            if source_key == "instagram":
                smart_queries = [
                    f"site:instagram.com {niche} {region} agendamento",
                    f"site:instagram.com {niche} {region} especialista",
                    f"site:instagram.com Dr Dra {niche} {region}",
                ]
            else:
                smart_queries = [
                    f"{niche} {region} agendamento whatsapp",
                    f"{niche} {region} endereco telefone",
                ]
        for sq in smart_queries[:4]:
            if len(leads) >= max_results:
                break
            try:
                results = _multi_engine_search(sq, 25, source_key=source_key)
                if not results:
                    continue
                verified_batch = _process_raw_results_parallel(
                    results, source_key, niche, region, block_large_portals, skip_domain,
                    seen_urls_local, previously_seen, max_results - len(leads)
                )
                for lead in verified_batch:
                    if len(leads) >= max_results:
                        break
                    if any(l["Link"].lower().strip().rstrip("/") == lead["Link"].lower().strip().rstrip("/") for l in leads):
                        continue
                    leads.append(lead)
                    print(f"[Scraper] +Lead Real Expandido: {_safe_str(lead['Nome'])[:40]} -> {_safe_str(lead['Link'])[:60]}")
                    if on_progress:
                        on_progress(len(leads), max_results, _safe_str(lead['Nome'])[:40])
            except Exception as e:
                print(f"[Scraper] Erro na busca expandida: {_safe_str(str(e))}")

    print(f"[Scraper] Fonte '{source_key}' retornou {len(leads)} leads 100% verificados")
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


def scrape_synthetic_direct(niche, region, sources, count, criteria=""):
    """
    Busca complementar com queries expandidas por IA + validacao HTTP/OpenGraph ao vivo.
    NUNCA inventa URLs sinteticas; retorna exclusivamente perfis e sites reais verificados.
    """
    source_key = "instagram" if "instagram" in str(sources).lower() else "maps"
    skip_domain = SOURCES.get(source_key, SOURCES["maps"]).get("skip_domain_filter", False)
    smart_queries = _generate_smart_queries(niche, region, source_key, criteria)
    if source_key == "instagram":
        smart_queries.extend([
            f"site:instagram.com {niche} {region} bio",
            f"site:instagram.com {niche} {region} atendimento",
            f"site:instagram.com {niche} {region}",
        ])
    else:
        smart_queries.extend([
            f"{niche} {region} whatsapp comercial",
            f"{niche} {region} telefone endereco",
        ])

    previously_seen = _get_previously_scraped_urls()
    seen_urls_local = set()
    leads = []

    for sq in list(dict.fromkeys(smart_queries))[:5]:
        if len(leads) >= count:
            break
        raw = _multi_engine_search(sq, max_results=max(count * 3, 20), source_key=source_key)
        if not raw:
            continue
        verified = _process_raw_results_parallel(
            raw, source_key, niche, region, True, skip_domain,
            seen_urls_local, previously_seen, count - len(leads)
        )
        for lead in verified:
            if len(leads) >= count:
                break
            if any(l["Link"].lower().strip().rstrip("/") == lead["Link"].lower().strip().rstrip("/") for l in leads):
                continue
            leads.append(lead)
    return leads


def scrape_leads(niche, region, sources=None, source=None, max_results=100, block_large_portals=True, on_progress=None, criteria="", **kwargs):
    sources = sources or source or ALL_SOURCES_KEY
    target_pool = max(int(max_results * 2.5), 15)

    print(f"\n{'='*60}")
    print(f"[Scraper V4] nicho='{niche}', regiao='{region}', fontes='{sources}', meta_bruta={target_pool} para obter {max_results} liquidos | Criterios: '{criteria}'")
    print(f"{'='*60}")

    previously_seen = _get_previously_scraped_urls()

    if isinstance(sources, str):
        source_keys = list(SOURCES.keys()) if sources == ALL_SOURCES_KEY else [sources]
    else:
        source_keys = sources

    if not source_keys:
        return []

    per_source = max(target_pool // len(source_keys), 12)

    batches_by_source = []
    executor = ThreadPoolExecutor(max_workers=min(len(source_keys), 4))
    try:
        future_to_source = {
            executor.submit(_scrape_single_source, niche, region, sk, per_source, block_large_portals, on_progress, previously_seen, criteria): sk
            for sk in source_keys
        }
        for future in as_completed(future_to_source, timeout=90):
            sk = future_to_source[future]
            try:
                batch = future.result()
                if batch:
                    batches_by_source.append(batch)
            except Exception as e:
                print(f"[Scraper] Fonte '{sk}' falhou: {e}")
    except Exception as e:
        print(f"[Scraper] Erro geral: {e}")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    # Intercalar leads de todas as fontes (round-robin)
    all_leads = []
    max_len = max((len(b) for b in batches_by_source), default=0)
    for idx in range(max_len):
        for b in batches_by_source:
            if idx < len(b):
                all_leads.append(b[idx])

    all_leads = deduplicate_leads(all_leads)
    print(f"[Scraper V4] FINAL: {len(all_leads)} leads unicos e 100% verificados obtidos")
    return all_leads[:target_pool]
