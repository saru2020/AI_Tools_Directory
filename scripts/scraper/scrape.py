#!/usr/bin/env python3
import csv
import time
import re
import os
import sys
import argparse
import random
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import yaml
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
import tldextract

# command: python scrape.py config.yaml --per-source 2000 --rate-limit 0.5 --verbose


try:
    # Pydantic v2
    from pydantic import BaseModel, HttpUrl, ValidationError, field_validator as _field_validator
    PD_V2 = True
except Exception:  # noqa: BLE001
    # Pydantic v1 fallback
    from pydantic import BaseModel, HttpUrl, ValidationError, validator as _validator
    PD_V2 = False


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg, flush=True)


TRACKING_QS = {"fbclid", "gclid", "yclid", "mc_cid", "mc_eid", "ref", "referrer"}


def clean_url(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str):
        return url
    try:
        s = urlparse(url)
        fragment = ""
        qs = []
        for k, v in parse_qsl(s.query, keep_blank_values=True):
            if k.lower().startswith("utm_"):
                continue
            if k.lower() in TRACKING_QS:
                continue
            qs.append((k, v))
        new_q = urlencode(qs, doseq=True)
        return urlunparse((s.scheme, s.netloc, s.path, s.params, new_q, fragment))
    except Exception:
        return url


def extract_domain(url: str) -> str:
    """Return registrable domain (eTLD+1), e.g., help.figma.com -> figma.com."""
    host = urlparse(url).netloc.strip().lower()
    if host.startswith("www."):
        host = host[4:]
    ext = tldextract.extract(host)
    if not ext.domain or not ext.suffix:
        return host.rstrip(".")
    return f"{ext.domain}.{ext.suffix}".rstrip(".")


def canonical_homepage(url: str) -> str:
    """Return a normalized homepage URL like https://example.com/ for any input URL."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.strip().lower()
        if host.startswith("www."):
            host = host[4:]
        ext = tldextract.extract(host)
        if ext.domain and ext.suffix:
            host = f"{ext.domain}.{ext.suffix}"
        scheme = "https"
        return f"{scheme}://{host}/"
    except Exception:
        return url


class FieldMap(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    pricing: Optional[str] = None
    logo: Optional[str] = None


class Source(BaseModel):
    name: str
    mode: str = "selectors"  # selectors | sitemap
    base_url: Optional[HttpUrl] = None
    list_selector: Optional[str] = None
    fields: Optional[FieldMap] = None
    sitemap_url: Optional[HttpUrl] = None
    limit: Optional[int] = 50


class Config(BaseModel):
    sources: List[Source]
    output_csv: str = "ai_tools_seed.csv"
    rate_limit_per_sec: float = 1.0
    user_agent: str = "AI-Tools-Dir-Scraper/1.0"
    request_timeout_sec: int = 20
    search_fallback: bool = True  # use web-search snippet if homepage lacks description
    use_llm: bool = False         # disabled by default per user request


class OutputRow(BaseModel):
    domain: str
    name: str
    description: Optional[str] = None
    website: HttpUrl
    category: Optional[str] = None
    pricing: Optional[str] = None
    logo: Optional[HttpUrl] = None
    source: Optional[str] = None

    if PD_V2:
        @_field_validator("name")
        @classmethod
        def _name_len_v2(cls, v: str) -> str:
            if len(v.strip()) < 3:
                raise ValueError("name too short")
            return v.strip()
    else:
        @_validator("name")
        def _name_len_v1(cls, v: str) -> str:
            if len(v.strip()) < 3:
                raise ValueError("name too short")
            return v.strip()


def select_text(el, selector: Optional[str]) -> Optional[str]:
    if not selector:
        return None
    attr = None
    if "@" in selector:
        selector, attr = selector.split("@", 1)
    target = el.select_one(selector.strip()) if selector.strip() else el
    if not target:
        return None
    if attr:
        return target.get(attr)
    return target.get_text(strip=True)


def normalize(row: Dict[str, Any]) -> Dict[str, Any]:
    row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
    if row.get("pricing"):
        row["pricing"] = row["pricing"].title()
    if row.get("category"):
        row["category"] = row["category"].title()
    if row.get("website") and isinstance(row["website"], str):
        if row["website"].startswith("//"):
            row["website"] = "https:" + row["website"]
        elif not re.match(r"^https?://", row["website"], re.I):
            row["website"] = "https://" + row["website"]
        row["website"] = clean_url(row["website"])  # strip tracking
    if row.get("logo") and isinstance(row["logo"], str):
        row["logo"] = clean_url(row["logo"])  # strip tracking
    return row


def best_paragraph(soup: BeautifulSoup) -> Optional[str]:
    # Choose the first meaningful paragraph (length heuristics, avoid menus/footers)
    for p in soup.find_all("p"):
        txt = p.get_text(" ", strip=True)
        if 60 <= len(txt) <= 300:
            # avoid obvious cookie or signup texts
            if re.search(r"cookies|subscribe|sign\s*up|newsletter|privacy", txt, re.I):
                continue
            return txt
    return None


def summarise_with_llm(text: str, max_chars: int = 240) -> Optional[str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not text:
        return None
    try:
        # Lightweight direct HTTP call to OpenAI Chat Completions (no extra deps)
        import json
        import requests as _rq

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Summarize the product in one clear sentence (<= 200 chars)."},
                {"role": "user", "content": text[:4000]},
            ],
            "temperature": 0.2,
            "max_tokens": 120,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        r = _rq.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=20)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"].strip()
        return content[:max_chars]
    except Exception:
        return None


def resolve_logo_from_homepage(home_url: str, soup: BeautifulSoup) -> Optional[str]:
    # Prefer largest rel icon sizes
    candidates: List[tuple[int, str]] = []
    for rel in ("icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed"):
        for link in soup.find_all("link", rel=lambda v: v and rel in v):
            href = link.get("href")
            if not href:
                continue
            sizes = link.get("sizes", "")
            size_val = 0
            if sizes and "x" in sizes:
                try:
                    size_val = max(int(x) for x in re.findall(r"(\d+)", sizes))
                except Exception:
                    size_val = 0
            abs_url = urljoin(home_url, href)
            candidates.append((size_val, abs_url))
    if candidates:
        # return largest
        return sorted(candidates, key=lambda x: x[0], reverse=True)[0][1]
    # Fallback to /favicon.ico
    parsed = urlparse(home_url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


def best_description_from_homepage(home_soup: BeautifulSoup) -> Optional[str]:
    # Prefer meta description
    md = home_soup.find("meta", attrs={"name": "description"}) or home_soup.find("meta", attrs={"property": "og:description"})
    desc = md.get("content").strip() if md and md.get("content") else None
    if desc and len(desc) >= 40:
        return desc[:280]
    # fallback to first meaningful paragraph
    p = best_paragraph(home_soup)
    if p:
        return p[:280]
    return None


EXCLUDED_URL_PATTERNS = (
    "privacy",
    "cookie",
    "cookies",
    "terms",
    "policy",
    "newsletter",
    "press",
    "newsroom",
    "/news/",
    "/blog/",
    "/notify/",
    "/dsar/",
    "aff_",
    "utm_",
    "?ref=",
)

EXCLUDED_DOMAINS = {
    # social/media/link-out domains we don't want as tool websites
    "youtube.com",
    "twitter.com",
    "x.com",
    "pinterest.com",
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "medium.com",
    # link shorteners/affiliates/trackers
    "go2cloud.org",
    "impact.com",
    "i384100.net",
    "grsm.io",
    "bit.ly",
    "tinyurl.com",
    "t.me",
    "telegram.me",
    "telegram.org",
    "fas.st",
    "pxf.io",
}


def _score_external_link(a_tag: Any, page_host: str) -> int:
    href = a_tag.get("href", "").strip()
    if not href:
        return -999
    if not re.match(r"^https?://", href, re.I):
        return -999
    target_host = urlparse(href).netloc.replace("www.", "").lower()
    if target_host == page_host:
        return -999
    # exclude unwanted domains
    if target_host in EXCLUDED_DOMAINS:
        return -500
    # exclude unwanted path patterns
    parsed = urlparse(href)
    path_q = (parsed.path + ("?" + parsed.query if parsed.query else "")).lower()
    for pat in EXCLUDED_URL_PATTERNS:
        if pat in path_q:
            return -200
    text = (a_tag.get_text(" ", strip=True) or "").lower()
    score = 0
    # positive signals
    if any(k in text for k in ("visit", "official", "website", "open", "launch", "try", "go to")):
        score += 50
    if a_tag.get("target") == "_blank":
        score += 5
    rel = a_tag.get("rel") or []
    if any(k in rel for k in ("noopener", "noreferrer")):
        score += 2
    # penalize long query strings (likely tracking / affiliate)
    if len(parsed.query) > 30:
        score -= 5
    # prefer shorter paths (homepage-ish)
    if parsed.path in ("", "/"):
        score += 20
    return score


def find_external_website(soup: BeautifulSoup, page_url: str) -> Optional[str]:
    page_host = urlparse(page_url).netloc.replace("www.", "").lower()
    best_href: Optional[str] = None
    best_score = -999
    for a in soup.find_all("a", href=True):
        s = _score_external_link(a, page_host)
        if s > best_score:
            best_score = s
            best_href = a.get("href", "")
    return best_href


def http_get(session: requests.Session, url: str, timeout: int, retries: int = 2, verbose: bool = False) -> requests.Response:
    last_e: Optional[Exception] = None
    for i in range(retries + 1):
        try:
            resp = session.get(url, timeout=timeout, headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
            })
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_e = e
            log(f"Retry {i+1} {url}: {e}", verbose)
            time.sleep(0.5 * (i + 1))
    raise last_e  # type: ignore[misc]


def search_snippet(session: requests.Session, domain: str, timeout: int, verbose: bool) -> Optional[str]:
    """Fetch a short snippet from DuckDuckGo HTML as a fallback description."""
    try:
        q = quote_plus(domain)
        url = f"https://duckduckgo.com/html/?q={q}"
        r = session.get(url, timeout=timeout, headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0"),
            "Cache-Control": "no-cache",
        })
        r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        # DuckDuckGo HTML layout: snippets have class 'result__snippet'
        sn = s.select_one(".result__snippet")
        txt = sn.get_text(" ", strip=True) if sn else None
        if txt and len(txt) >= 40:
            return txt[:280]
        return None
    except Exception as e:
        log(f"[search] failed {domain}: {e}", verbose)
        return None


def extract_name_from_homepage(home_soup: BeautifulSoup, domain: str) -> str:
    """Extract the best name from homepage, fallback to domain."""
    # Try meta title first
    og_title = home_soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
        if len(title) >= 3 and not title.lower().startswith(("privacy", "terms", "cookie")):
            return title[:100]
    
    # Try h1
    h1 = home_soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
        if len(title) >= 3 and not title.lower().startswith(("privacy", "terms", "cookie")):
            return title[:100]
    
    # Try page title
    if home_soup.title:
        title = home_soup.title.get_text(strip=True)
        if len(title) >= 3 and not title.lower().startswith(("privacy", "terms", "cookie")):
            return title[:100]
    
    # Fallback to domain name without extension
    domain_parts = domain.split(".")
    if len(domain_parts) >= 2:
        return domain_parts[-2].title()
    return domain.title()


def extract_metadata(session: requests.Session, url: str, source_name: str, cfg: Config, verbose: bool) -> Dict[str, Any]:
    # Fetch competitor listing page
    resp = http_get(session, url, timeout=cfg.request_timeout_sec, verbose=verbose)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Resolve external official website (preferred) or canonical
    ext_site = find_external_website(soup, url)
    canon_link = soup.find("link", rel="canonical")
    canon = canon_link.get("href").strip() if canon_link and canon_link.get("href") else url
    website = ext_site if ext_site else canon
    website = clean_url(website) or website
    homepage = canonical_homepage(website)

    # Fetch homepage to improve description and logo
    home_soup = None
    try:
        home_resp = http_get(session, homepage, timeout=cfg.request_timeout_sec, verbose=verbose)
        home_soup = BeautifulSoup(home_resp.text, "html.parser")
    except Exception:
        home_soup = None

    # Get name from homepage (preferred) or listing page (fallback)
    name = None
    if home_soup:
        name = extract_name_from_homepage(home_soup, extract_domain(website))
    else:
        # Fallback to listing page title
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            name = og_title["content"].strip()
        elif soup.title:
            name = soup.title.get_text(strip=True)
        if not name or len(name) < 3:
            name = extract_name_from_homepage(soup, extract_domain(website))

    # Choose best description from homepage
    desc = best_description_from_homepage(home_soup) if home_soup else None

    # Optional web-search fallback (no LLM)
    if (not desc or len(desc) < 40) and cfg.search_fallback:
        dom = extract_domain(homepage)
        ss = search_snippet(session, dom, cfg.request_timeout_sec, verbose)
        if ss:
            desc = ss

    # Resolve logo from homepage
    logo = resolve_logo_from_homepage(homepage, home_soup) if home_soup else None

    # Basic category from keywords on homepage
    kw = home_soup.find("meta", attrs={"name": "keywords"}) if home_soup else None
    category = kw.get("content").split(",")[0].strip().title() if kw and kw.get("content") else None

    return normalize({
        "name": name,
        "description": desc,
        "website": homepage,
        "category": category,
        "pricing": None,
        "logo": logo,
        "source": source_name,
    })


def parse_sitemap_urls(session: requests.Session, sitemap_url: str, limit: int, cfg: Config, verbose: bool) -> List[str]:
    urls: List[str] = []
    resp = http_get(session, sitemap_url, timeout=cfg.request_timeout_sec, verbose=verbose)
    soup = BeautifulSoup(resp.text, "xml")
    if soup.find("sitemapindex"):
        nested = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
        for sm in nested:
            if sm.endswith(".xml"):
                try:
                    resp2 = http_get(session, sm, timeout=cfg.request_timeout_sec, verbose=verbose)
                    s2 = BeautifulSoup(resp2.text, "xml")
                    for loc in s2.find_all("loc"):
                        url = loc.get_text(strip=True)
                        if not url.endswith(".xml"):
                            urls.append(url)
                            if len(urls) >= limit:
                                return urls
                except Exception as e:
                    log(f"[sitemap] nested fetch failed {sm}: {e}", verbose)
        return urls
    for loc in soup.find_all("loc"):
        url = loc.get_text(strip=True)
        if url.endswith(".xml"):
            continue
        urls.append(url)
        if len(urls) >= limit:
            break
    return urls


def scrape_sitemap(session: requests.Session, src: Source, cfg: Config, verbose: bool) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not src.sitemap_url:
        return rows
    print(f"Processing source: {src.name}")
    urls = parse_sitemap_urls(session, str(src.sitemap_url), src.limit or 500, cfg, verbose)
    for i, url in enumerate(urls, 1):
        try:
            row = extract_metadata(session, url, src.name, cfg, verbose)
            if row.get("name"):
                rows.append(row)
        except Exception as e:
            log(f"[{src.name}] failed {url}: {e}", verbose)
        if i % 25 == 0:
            print(f"{src.name}: {i}/{len(urls)}", flush=True)
    return rows


def scrape_selectors(session: requests.Session, src: Source, cfg: Config, verbose: bool) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    print(f"Processing source: {src.name}")
    resp = http_get(session, str(src.base_url), timeout=cfg.request_timeout_sec, verbose=verbose)
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(src.list_selector or "")
    for card in cards:
        row = {
            "name": select_text(card, src.fields.name if src.fields else None),
            "description": select_text(card, src.fields.description if src.fields else None),
            "website": select_text(card, src.fields.website if src.fields else None),
            "category": select_text(card, src.fields.category if src.fields else None),
            "pricing": select_text(card, src.fields.pricing if src.fields else None),
            "logo": select_text(card, src.fields.logo if src.fields else None),
            "source": src.name,
        }
        row = {k: (v[:280] if isinstance(v, str) else v) for k, v in row.items()}
        if row.get("name") and row.get("website"):
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to config.yaml")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--per-source", type=int, default=None)
    parser.add_argument("--rate-limit", type=float, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg_raw = yaml.safe_load(f)
    try:
        cfg = Config(**cfg_raw)
    except ValidationError as e:
        print("Invalid config:", e, file=sys.stderr)
        return 2

    if args.rate_limit is not None:
        cfg.rate_limit_per_sec = args.rate_limit
    if args.timeout is not None:
        cfg.request_timeout_sec = args.timeout
    if args.per_source is not None:
        for s in cfg.sources:
            s.limit = args.per_source

    headers = {"User-Agent": cfg.user_agent}
    session = requests.Session()
    session.headers.update(headers)

    fieldnames = ["domain", "name", "description", "website", "category", "pricing", "logo", "source"]
    written_domains: set[str] = set()
    written_count = 0
    with open(cfg.output_csv, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        for src in cfg.sources:
            try:
                rows = scrape_sitemap(session, src, cfg, args.verbose) if src.mode == "sitemap" else scrape_selectors(session, src, cfg, args.verbose)
                print(f"Validating {len(rows)} rows from {src.name}")
                for r in rows:
                    try:
                        if not r.get("website"):
                            continue
                        dom = extract_domain(str(r["website"]))
                        if not dom or dom in written_domains:
                            continue
                        r["domain"] = dom
                        if r.get("description") and len(str(r["description"])) > 300:
                            r["description"] = str(r["description"])[:300]
                        r = {k: (clean_url(v) if k in ("website", "logo") else v) for k, v in r.items()}
                        orow = OutputRow(**r)
                        writer.writerow(orow.model_dump() if hasattr(orow, "model_dump") else orow.dict())
                        written_domains.add(dom)
                        written_count += 1
                    except ValidationError:
                        continue
            except Exception as e:
                log(f"[ERROR] Source {src.name} failed: {e}", args.verbose)
            time.sleep(1.0 / max(cfg.rate_limit_per_sec, 0.1))

    print(f"Wrote {written_count} rows to {cfg.output_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
