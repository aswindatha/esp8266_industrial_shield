#!/usr/bin/env python3
"""
search_robu.py — robu.in component finder (v2, API-driven).

Searches robu.in via its internal JSON API (POST /api/search/) from
inside a real Chrome session — one navigation clears the Cloudflare
challenge, then every query/detail is an in-page fetch: ~1 s per
search and one batched round-trip for all product pages.

Smart ranking: keyword + synonym match on name/MPN/short_description/
category, numeric feature match (pins/pitch/V/A/MHz/GB) with mismatch
penalty, spec-table verification, confidence flag, and budget
preference — cheapest in-stock item among the best matches wins.

Usage:
    python search_robu.py "4 pin 5mm pluggable screw terminal"
    python search_robu.py "60v buck" "4g lte antenna" --top 3 --json
    python search_robu.py "rtc module" --fast          # API data only
    python search_robu.py "100nF 0805" "LTV-356T" --qty 20,4 --table

Requires: pip install DrissionPage beautifulsoup4  (Chrome/Edge installed)
"""

import argparse
import io
import json
import re
import sys
import time
from urllib.parse import quote_plus

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # detail fetching degrades gracefully

SEARCH_API = "/api/search/"
GRAPHQL_API = "/api/proxy/graphql/"
BASE = "https://robu.in"

PRODUCT_GQL = """query PD($slug: String!) {
  productdetails(slug: $slug) {
    data {
      id sku name url_key in_stock available_quantity is_backorder
      price { regular final special }
      moq_prices { range_from range_to price }
      additional { key value }
      description short_description
      categories { name }
      product_brand { name }
      attachments { title file_path }
    }
  }
}"""
CF_WAIT_S = 60
FETCH_POLL_S = 0.4
FETCH_TIMEOUT_S = 30

STOPWORDS = {
    "a", "an", "the", "for", "with", "and", "or", "of", "to", "in",
    "module", "board", "component", "components", "pcs", "pc", "pack",
    "type", "new", "original", "best", "price", "buy", "online", "india",
}

# query/candidate synonym expansion (both directions)
ALIASES = {
    "buck": ["step-down", "stepdown", "converter", "dc-dc", "dcdc"],
    "step": ["buck", "converter"],
    "boost": ["step-up", "stepup", "converter"],
    "microsd": ["sd", "tf", "memory", "micro-sd"],
    "sd": ["microsd", "tf", "memory"],
    "anemometer": ["wind", "speed"],
    "terminal": ["terminal-block", "screw-terminal", "connector", "block"],
    "antenna": ["aerial", "whip", "antenna"],
    "psu": ["power", "supply", "adapter", "smps"],
    "gland": ["cable-gland", "pg"],
    "lora": ["sx126", "sx127", "e22"],
    "rtc": ["ds3231", "real-time", "clock"],
    "endurance": ["high-endurance", "industrial"],
    "sim": ["gsm", "lte", "4g", "gprs"],
    "lte": ["4g", "gsm", "cellular"],
    "4g": ["lte", "gsm", "cellular"],
    "solar": ["mppt", "pwm", "charge", "charger"],
    "enclosure": ["box", "junction", "case", "housing"],
    "junction": ["box", "enclosure"],
    "moisture": ["humidity", "soil", "hygrometer"],
    "particulate": ["pm2.5", "pm10", "dust", "sps30"],
    "screw": ["terminal", "block"],
    "pluggable": ["plug", "connector"],
    "sensor": ["module", "probe", "detector"],
}


def _norm(s):
    """Tokens: original alnum words (keeps rs485, sps30, bme688 intact)
    PLUS digit/letter-boundary splits (60v → 60, v)."""
    s = s.lower()
    orig = re.findall(r"[a-z0-9.]+", s)
    s2 = re.sub(r"([a-z])(\d)", r"\1 \2", s)
    s2 = re.sub(r"(\d)([a-z])", r"\1 \2", s2)
    return list(set(orig) | set(re.findall(r"[a-z0-9.]+", s2)))


def _fnum(x):
    try:
        return str(float(x)).rstrip("0").rstrip(".")
    except ValueError:
        return x


def _features(text):
    """Numeric feature sets: pins, pitch mm, volts, amps, MHz, GB."""
    t = text.lower()
    f = lambda pat: {_fnum(x) for x in re.findall(pat, t)}
    pins = f(r"(\d+)\s*[-x]?\s*(?:pin|way|pos(?:ition)?s?|pole|channel|relay|p)\b")
    pins |= f(r"\b(\d{1,2})p\b")
    pitch = f(r"(\d(?:\.\d+)?)\s*mm\b")
    volts = f(r"(\d+(?:\.\d+)?)\s*v(?:olt|dc)?\b")
    amps = f(r"(\d+(?:\.\d+)?)\s*a(?:mp)?\b")
    mhz = f(r"(\d+(?:\.\d+)?)\s*(?:mhz|ghz)\b")
    gb = f(r"(\d+)\s*(?:gb|g\b)")
    return {"pin": pins, "pitch": pitch, "V": volts, "A": amps,
            "MHz": mhz, "GB": gb}


def _expand(tokens):
    out = set(tokens)
    for t in tokens:
        out.update(ALIASES.get(t, ()))
    return out


def score(query, cand, cand_features):
    """(score, matched, mismatched). Title/MPN/category hits = 2 pts,
    description-only hits = 0.5 — keeps decoys (spec-sheet buzzwords)
    from outranking real matches."""
    primary = " ".join([cand.get("title") or "", cand.get("mpn") or ""]).lower()
    secondary = " ".join([cand.get("short_desc") or "",
                          " ".join(cand.get("categories") or [])]).lower()
    ct_p, ct_s = set(_norm(primary)), set(_norm(secondary))
    qt = [w for w in _norm(query)
          if w not in STOPWORDS and not (len(w) == 1 and w.isalpha())]
    p_hit, s_hit = [], []
    for w in qt:
        grp = {w} | set(ALIASES.get(w, ()))
        grp = {g for g in grp if len(g) > 1}
        if w in ct_p or any(g in primary for g in grp if len(g) > 2):
            p_hit.append(w)
        elif w in ct_s or any(g in secondary for g in grp if len(g) > 2):
            s_hit.append(w)
    s = 2 * len(p_hit) + 0.5 * len(s_hit)
    func_q = [w for w in qt
              if not w.replace(".", "").isdigit()
              and not (any(c.isdigit() for c in w) and any(c.isalpha() for c in w))]
    func_hit = [m for m in p_hit
                if not m.replace(".", "").isdigit()
                and not (any(c.isdigit() for c in m) and any(c.isalpha() for c in m))]
    if func_q and not func_hit:                 # wrong kind of part entirely
        s -= 3
    matched = p_hit + s_hit
    qf = _features(query)
    mismatched = []
    for cls, qvals in qf.items():
        if not qvals:
            continue
        cvals = cand_features.get(cls, set())
        if cvals & qvals:
            s += 3 if cls in ("pin", "pitch") else 2
        elif cvals:
            s -= 3 if cls in ("pin", "pitch") else 2
            mismatched.append(cls)
    return s, matched, mismatched


TECH_TOKENS = {
    "rs485", "rs232", "rs422", "uart", "spi", "i2c", "iic", "can",
    "modbus", "sma", "ipex", "ipx", "u.fl", "zh", "xh", "ph", "vh",
    "gpio", "adc", "dac", "pwm", "mppt", "ttl", "rs485-modbus",
}


def _distinctive(query):
    """High-signal tokens (rs485, sma, i2c, sps30…) — must appear in a
    correct match, so unmatched ones justify widening the search."""
    return [w for w in _norm(query)
            if (any(ch.isdigit() for ch in w) and any(ch.isalpha() for ch in w)
                and len(w) > 2) or w in TECH_TOKENS]


# ---------------------------------------------------------------- browser

class _Browser:
    """One Chrome window; first nav clears Cloudflare, then fetch() all."""

    def __init__(self):
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
        except ImportError:
            sys.exit("DrissionPage missing: pip install DrissionPage")
        co = ChromiumOptions()
        # own debug port + temp profile per run: two concurrent instances
        # otherwise attach to the same Chrome and corrupt each other's
        # in-page fetch results
        co.auto_port()
        co.set_argument("--window-position=2000,2000")
        co.set_argument("--window-size=1100,800")
        self.pg = ChromiumPage(co)
        self._ready = False

    def _ensure(self):
        if self._ready:
            return
        self.pg.get(BASE + "/")
        for _ in range(int(CF_WAIT_S / 0.5)):
            if "moment" not in (self.pg.title or "").lower():
                break
            time.sleep(0.5)
        self._ready = True

    def fetch_json(self, path, payload=None, timeout=FETCH_TIMEOUT_S, retries=2):
        """In-page fetch → parsed JSON (works for same-origin robu APIs).

        Cloudflare can swap an API response for an HTML interstitial; the
        .json() parse then rejects, so re-navigate to renew the clearance
        cookie and retry instead of silently degrading to page scraping.
        """
        body = ("JSON.stringify(" + json.dumps(payload) + ")") if payload else "undefined"
        method = "POST" if payload else "GET"
        js = (
            'window.__rr=null;fetch("' + path + '",{method:"' + method + '",'
            'headers:{"Content-Type":"application/json"},credentials:"include",'
            'body:' + body + '}).then(r=>r.json()).then(d=>{window.__rr=d})'
            '.catch(e=>{window.__rr={__err:String(e)}});return 1'
        )
        res = None
        for attempt in range(retries + 1):
            self._ensure()
            self.pg.run_js(js)
            res = self._await(timeout)
            if isinstance(res, dict) and "__err" not in res:
                return res
            if attempt < retries:
                self._ready = False          # force a fresh navigation
                time.sleep(1.0)
        return res

    def gql_batch(self, slugs, timeout=FETCH_TIMEOUT_S):
        """ProductDetails for many slugs in ONE Promise.all round-trip."""
        self._ensure()
        js = (
            'window.__rr=null;Promise.all(' + json.dumps(slugs) +
            '.map(s=>fetch("' + GRAPHQL_API + '",{method:"POST",'
            'headers:{"Content-Type":"application/json"},credentials:"include",'
            'body:JSON.stringify({query:' + json.dumps(PRODUCT_GQL) +
            ',variables:{slug:s}})}).then(r=>r.json())'
            '.then(d=>({s,d})).catch(e=>({s,e:String(e)})))'
            ').then(d=>{window.__rr=d});return 1'
        )
        self.pg.run_js(js)
        res = self._await(timeout)
        out = {}
        for item in res or []:
            if "d" in item:
                out[item["s"]] = item["d"]
        return out

    def fetch_html_batch(self, urls, timeout=FETCH_TIMEOUT_S):
        """One round-trip for many pages → {url: html}."""
        self._ensure()
        js = (
            'window.__rr=null;Promise.all(' + json.dumps(urls) +
            '.map(u=>fetch(u,{credentials:"include"})'
            '.then(r=>r.text()).then(t=>({u,t})).catch(e=>({u,e:String(e)})))'
            ').then(d=>{window.__rr=d});return 1'
        )
        self.pg.run_js(js)
        res = self._await(timeout)
        out = {}
        for item in res or []:
            if "t" in item:
                out[item["u"]] = item["t"]
        return out

    def _await(self, timeout=FETCH_TIMEOUT_S):
        t0 = time.time()
        while time.time() - t0 < timeout:
            r = self.pg.run_js("return window.__rr")
            if r is not None:
                return r
            time.sleep(FETCH_POLL_S)
        return None

    # legacy navigation fallback (only if the API ever breaks)
    def get_page(self, url):
        self._ensure()
        self.pg.get(url)
        js = ('return Array.from(document.querySelectorAll("a"))'
              '.filter(a=>a.href.includes("/product/")).length')
        for _ in range(30):
            if self.pg.run_js(js) > 3:
                break
            time.sleep(0.5)
        return self.pg.html

    def close(self):
        try:
            self.pg.quit()
        except Exception:
            pass


# ---------------------------------------------------------------- parsing

_PRICE_RE = re.compile(r"₹\s*([\d,]+(?:\.\d+)?)")


def _money(s):
    m = _PRICE_RE.search((s or "").replace(",", ""))
    return float(m.group(1)) if m else None


def api_search(browser, query, limit=50, semantic=False, offset=0):
    """POST /api/search/ → list of product dicts (robu schema).
    Falls back to scraping search tiles if the API errors."""
    r = browser.fetch_json(SEARCH_API, {
        "q": query, "limit": limit, "offset": offset, "sort": "",
        "semantic": semantic})
    prods = ((r or {}).get("data") or {}).get("products")
    if prods is None:                                  # API failed → scrape
        html = browser.get_page(
            BASE + "/?s=" + quote_plus(query) + "&post_type=product")
        return scrape_tiles(html), 0
    out = []
    for p in prods:
        slug = re.sub(r"[^a-z0-9\-]+", "-", (p.get("slug") or "").lower()).strip("-")
        out.append({
            "id": p.get("id"),
            "slug": slug,
            "title": p.get("name"),
            "url": f"{BASE}/product/{slug}/" if slug else None,
            "price": p.get("price"),
            "regular_price": p.get("regular_price"),
            "in_stock": bool(p.get("in_stock")),
            "sku": p.get("sku"),
            "mpn": p.get("mpn"),
            "categories": p.get("category_names") or [],
            "short_desc": re.sub(r"\s+", " ", p.get("short_description") or "").strip(),
            "moq_prices": p.get("moq_prices") or [],
            "sales_count": p.get("sales_count") or 0,
            "rating": p.get("reviews_rating") or 0,
            "exact_sku_match": bool(p.get("exact_sku_match")),
        })
    return out, ((r or {}).get("data") or {}).get("total_products", 0)


_SKU_RE = re.compile(r"SKU:\s*([A-Za-z0-9\-]+)")


def scrape_tiles(html):
    """Fallback: parse .product-block tiles from a rendered search page."""
    if not html or not BeautifulSoup:
        return []
    soup = BeautifulSoup(html, "html.parser")
    tiles = []
    for block in soup.select(".product-block"):
        a = block.find("a", href=lambda h: h and "/product/" in h)
        if not a:
            continue
        text = re.sub(r"\s+", " ", block.get_text(" ", strip=True))
        sku = _SKU_RE.search(text)
        slug = a["href"].split("?")[0].rstrip("/").rsplit("/", 1)[-1]
        title = re.split(r"SKU:|₹|\(\s*\d+\s*(?:customer|review|\))", text)[0].strip(" -")
        tiles.append({
            "id": None, "slug": slug, "title": title,
            "url": f"{BASE}/product/{slug}/",
            "price": _money(text), "regular_price": None,
            "in_stock": "out of stock" not in text.lower(),
            "sku": sku.group(1) if sku else None, "mpn": None,
            "categories": [], "short_desc": "", "moq_prices": [],
            "sales_count": 0, "rating": 0, "exact_sku_match": False,
        })
    return tiles


def _strip_html(s):
    if not s or not BeautifulSoup:
        return re.sub(r"<[^>]+>", " ", s or "")
    return BeautifulSoup(s, "html.parser").get_text(" ", strip=True)


SPEC_JUNK = re.compile(
    r"^(Meta |Shipping (Class|Length|Width|Height|Weight)|Custom Backorder|"
    r"Tax Class|Length$|Width$|Height$|SKU|Name$|URL Key|Featured|Visible|"
    r"Status$|Short Description$|Description$|Special Price|Image|Base Image|"
    r"Small Image|Thumbnail|Gallery|Media|Video$)", re.I)


def gql_product(resp, slug):
    """Parse one ProductDetails GraphQL response into our detail dict."""
    d = (((resp or {}).get("data") or {}).get("productdetails") or {}).get("data")
    if not d:
        return {}
    specs, extra, ship = {}, {}, {}
    for a in d.get("additional") or []:
        k, v = (a.get("key") or "").rstrip(":"), a.get("value")
        if not k or v in (None, ""):
            continue
        if k in ("Short Description", "Description"):
            extra[k] = v
        elif k.startswith("Shipping "):
            ship[k] = v
        elif not SPEC_JUNK.match(k):
            specs[k] = v
    price = d.get("price") or {}
    brand = d.get("product_brand")
    if isinstance(brand, list):
        brand = brand[0] if brand else {}
    dim = next((specs[k] for k in specs if "dimension" in k.lower()), None)
    if not dim and all(k in ship for k in ("Shipping Length", "Shipping Width", "Shipping Height")):
        dim = " × ".join(ship[k] for k in ("Shipping Length", "Shipping Width", "Shipping Height")) + " cm"
    wgt = ship.get("Shipping Weight") or next(
        (specs[k] for k in specs if "weight" in k.lower()), None)
    if wgt and re.fullmatch(r"[\d.]+", str(wgt)):
        wgt = f"{wgt} kg"
    return {
        "title": d.get("name"),
        "url": f"{BASE}/product/{d.get('url_key') or slug}/",
        "price": price.get("final") or price.get("regular"),
        "regular_price": price.get("regular"),
        "in_stock": bool(d.get("in_stock")),
        "qty": d.get("available_quantity"),
        "sku": d.get("sku"),
        "specs": specs,
        "moq_prices": d.get("moq_prices") or [],
        "shipping_dims": dim,
        "shipping_weight": wgt,
        "brand": (brand or {}).get("name") if isinstance(brand, dict) else brand,
        "datasheet": next((a.get("file_path") for a in (d.get("attachments") or [])
                          if a.get("file_path")), None),
        "description": _strip_html(d.get("description") or extra.get("Description")),
        "short_desc": re.sub(r"\s+", " ", _strip_html(
            d.get("short_description") or extra.get("Short Description"))).strip(),
    }


# ---------------------------------------------------------------- ranking

def _cand_text(c):
    return " ".join([c.get("title") or "", c.get("mpn") or "",
                     " ".join(c.get("categories") or []),
                     c.get("short_desc") or ""])


def pick_best(candidates, query):
    """Annotate scores; recommended = in-stock, top relevance, cheapest."""
    for c in candidates:
        cf = _features(_cand_text(c))
        s, matched, mismatched = score(query, c, cf)
        if c.get("exact_sku_match"):
            s += 5
        if any(w in " ".join(c.get("categories") or []).lower()
               for w in _norm(query) if len(w) > 3):
            s += 1
        s += min(2, (c.get("sales_count") or 0) // 50)   # tiny popularity tiebreak
        c.update(score=s, matched=matched, mismatched=mismatched,
                 feats={k: sorted(v) for k, v in cf.items()})
    pool = [c for c in candidates if c["in_stock"] and c["price"]]
    if not pool:
        pool = [c for c in candidates if c["price"]]
    if not pool:
        return None, candidates
    top = max(c["score"] for c in pool)
    near = [c for c in pool
            if c["score"] >= max(top - 3, top * 0.6) and not c["mismatched"]]
    if not near:                                  # all top hits mismatched
        near = [c for c in pool if c["score"] >= top - 2]
    near.sort(key=lambda c: c["price"])           # budget preference
    return near[0], sorted(candidates, key=lambda c: (-c["score"], c["price"] or 9e9))


def verify(c, query):
    """Cross-check query's numeric features against fetched specs/desc."""
    qf = _features(query)
    cf = c.get("feats") or _features(_cand_text(c))
    spec_text = " ".join(f"{k} {v}" for k, v in (c.get("specs") or {}).items())
    sf = _features(spec_text + " " + (c.get("description") or "") + " " + _cand_text(c))
    confirmed, conflict = [], []
    for cls, qvals in qf.items():
        if not qvals:
            continue
        if set(sf.get(cls) or ()) & qvals:
            confirmed.append(cls)
        elif sf.get(cls):
            conflict.append(cls)
    if conflict:
        conf = "low"
    elif c.get("in_stock") and (confirmed or c.get("score", 0) >= 4):
        conf = "high" if confirmed else "medium"
    elif c.get("in_stock"):
        conf = "medium" if c.get("score", 0) >= 2 else "low"
    else:
        conf = "low"
    c.update(confirmed=confirmed, conflict=conflict, confidence=conf)
    return c


def _relax(query):
    """Drop the last informative token; None when nothing left to drop."""
    toks = [w for w in query.split() if w.lower() not in STOPWORDS]
    if len(toks) <= 1:
        return None
    toks.pop()
    return " ".join(toks)


# ---------------------------------------------------------------- main API

def robu_search(browser, query, limit=50, top=3, fast=False, relax=True):
    t0 = time.time()
    used, tries = query, []
    candidates, total = [], 0
    while True:
        tries.append(used)
        candidates, total = api_search(browser, used, limit)
        if candidates or not relax:
            break
        nxt = _relax(used)
        if not nxt:
            break
        used = nxt
    best, ranked = pick_best(candidates, query)

    # widen the net when a distinctive token (rs485, sma, zh…) is
    # unmatched in every fetched candidate: page 2, then semantic retry
    dist = set(_distinctive(query))
    def unmatched_dist():
        hit = set()
        for c in candidates[:50]:
            hit.update(w for w in dist if w in _norm(_cand_text(c)))
        return dist - hit

    if relax and unmatched_dist() and total > len(candidates):
        more, _ = api_search(browser, used, limit, offset=len(candidates))
        seen = {c["id"] for c in candidates}
        candidates += [c for c in more if c["id"] not in seen]
        best, ranked = pick_best(candidates, query)

    semantic_used = False
    if relax and (best is None or best.get("score", 0) < 3 or unmatched_dist()):
        sem, _ = api_search(browser, query, limit, semantic=True)
        if sem:
            sbest, sranked = pick_best(sem + [c for c in candidates
                                            if c["id"] not in {s["id"] for s in sem}], query)
            # accept only a genuine match — otherwise a gibberish query
            # comes back with random in-stock parts
            if sbest and sbest["score"] >= 2 and (best is None or sbest["score"] > best["score"]):
                best, ranked = sbest, sranked
                candidates = sem + candidates
                semantic_used = True
    ranked = list({c["url"]: c for c in ranked if c.get("url")}.values())

    details = []
    if not fast and ranked:
        slugs = [c["slug"] for c in ranked[:max(top, 1)] if c.get("slug")]
        resps = browser.gql_batch(slugs)
        for c in ranked[:max(top, 1)]:
            d = gql_product(resps.get(c.get("slug")), c.get("slug"))
            merged = {**c, **{k: v for k, v in d.items() if v not in (None, {}, "")}}
            details.append(verify(merged, query))
    else:
        details = [verify(dict(c), query) for c in ranked[:max(top, 1)]]

    best_full = next((d for d in details if best and d["url"] == best["url"]),
                     verify(dict(best), query) if best else None)
    return {"query": query, "query_used": used, "tries": tries,
            "semantic_used": semantic_used,
            "total_hits": total, "tile_count": len(candidates),
            "elapsed_s": round(time.time() - t0, 2),
            "best": best_full, "candidates": details}


def _fmt(d):
    if not d:
        return "  (no result)\n"
    conf = d.get("confidence", "?")
    stock = f"In stock ({d['qty']} pcs)" if d.get("in_stock") and d.get("qty") else \
            ("In stock" if d.get("in_stock") else "OUT OF STOCK")
    out = [f"  [{conf.upper()}] {d.get('title')}",
           f"  URL   : {d['url']}",
           f"  Price : ₹{d.get('price')}  |  {stock}"
           f"  |  SKU {d.get('sku')}" + (f"  |  MPN {d['mpn']}" if d.get("mpn") else "")
           + (f"  |  {d['brand']}" if d.get("brand") else "")]
    if (d.get("bom_qty") or 1) > 1 and d.get("ext_price") is not None:
        out.append(f"  Ext   : ₹{d['ext_price']:,.2f} for {d['bom_qty']} pcs"
                   f"  (@₹{d.get('unit_price_at_qty'):g}, tier {d.get('price_tier') or '?'})")
    if d.get("shortfall"):
        out.append(f"  !! only {d.get('qty')} pcs in stock — short by {d['shortfall']}")
    if d.get("datasheet"):
        out.append(f"  Doc   : {d['datasheet']}")
    if d.get("shipping_dims"):
        out.append(f"  Ship  : {d['shipping_dims']}, {d.get('shipping_weight')}")
    for k, v in (d.get("specs") or {}).items():
        out.append(f"    - {k}: {v}")
    for b in (d.get("moq_prices") or [])[:4]:
        lo, hi = b.get("range_from"), b.get("range_to")
        out.append(f"    bulk {lo}-{hi if hi and hi < 100000 else '+'}: ₹{b.get('price')}")
    if d.get("conflict"):
        out.append(f"    !! conflicts on: {', '.join(d['conflict'])}")
    return "\n".join(out) + "\n"


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _md(s):
    return re.sub(r"\s+", " ", str(s or "")).replace("|", "\\|")


def _unit_at_qty(d, n):
    """(unit_price, tier_from, tier_to) for buying n pcs."""
    tiers = d.get("moq_prices") or []
    cands = []
    for t in tiers:
        lo, hi = t.get("range_from") or 1, t.get("range_to")
        if n >= lo and (not hi or hi >= 100000 or n <= hi):
            cands.append(t)
    if cands:
        p = max(cands, key=lambda t: t.get("range_from") or 1)
        return _num(p.get("price")), p.get("range_from") or 1, p.get("range_to")
    return _num(d.get("price")), None, None


def apply_qty(r, n):
    """Attach BOM quantity, tier unit price and extended cost to a result."""
    r["bom_qty"] = n
    d = r.get("best")
    if not d:
        return
    unit, lo, hi = _unit_at_qty(d, n)
    d["bom_qty"] = n
    d["unit_price_at_qty"] = unit
    d["price_tier"] = f"{lo}-{hi if hi and hi < 100000 else '+'}" if lo else None
    d["ext_price"] = round(unit * n, 2) if unit is not None else None
    have = d.get("qty")
    if have and n > have:
        d["shortfall"] = n - have


def _parse_qtys(spec, n):
    vals = []
    for p in str(spec).split(","):
        p = p.strip()
        if p:
            try:
                vals.append(max(1, int(p)))
            except ValueError:
                vals.append(1)
    if not vals:
        vals = [1]
    while len(vals) < n:
        vals.append(vals[-1])
    return vals[:n]


def _report(results):
    chunks = []
    for r in results:
        head = f"### {r['query']}"
        if r.get("query_used") and r["query_used"] != r["query"]:
            head += f"  → relaxed to \"{r['query_used']}\""
        if r.get("semantic_used"):
            head += "  [semantic]"
        head += f"  ({r.get('total_hits','?')} hits, {r.get('tile_count')} shown, {r.get('elapsed_s','?')}s)"
        chunk = [head, "BEST:", _fmt(r["best"])]
        if r["candidates"]:
            chunk.append("ALTERNATES:")
            for c in r["candidates"][1:]:
                chunk.append(_fmt(c))
        chunks.append("\n".join(chunk))
    return "\n".join(chunks)


def _table(results):
    """One markdown row per BOM line — paste straight into a sourcing doc."""
    rows = ["| # | Query | Best match | SKU | Qty | Unit ₹ | Ext ₹ | Stock | Conf | Link |",
            "|---|-------|------------|-----|-----|--------|-------|-------|------|------|"]
    total, ok, missing = 0.0, 0, 0
    for i, r in enumerate(results, 1):
        q = r.get("bom_qty") or 1
        if r.get("error"):
            rows.append(f"| {i} | {_md(r['query'])} | ERROR: {_md(r['error'])} | | {q} | | | | | |")
            missing += 1
            continue
        d = r.get("best")
        if not d:
            rows.append(f"| {i} | {_md(r['query'])} | — no match | | {q} | | | | | |")
            missing += 1
            continue
        unit, ext = d.get("unit_price_at_qty"), d.get("ext_price")
        if ext is not None:
            total += ext
        stock = ("OUT" if not d.get("in_stock") else
                 (f"{d['qty']} pcs" if d.get("qty") else "in stock"))
        if d.get("shortfall"):
            stock += f" — short {d['shortfall']}"
        rows.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            i, _md(r["query"]), _md(d.get("title")), d.get("sku") or "", q,
            f"{unit:,.2f}" if unit is not None else "—",
            f"{ext:,.2f}" if ext is not None else "—",
            stock, (d.get("confidence") or "?").upper(), d.get("url") or ""))
        ok += 1
    rows += ["",
             f"**{ok} line(s) sourced, {missing} unmatched — estimated total "
             f"₹{total:,.2f}** (incl. GST, checked {time.strftime('%Y-%m-%d')}; "
             f"confirm stock before ordering)"]
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description="Search robu.in for components")
    ap.add_argument("query", nargs="+", help="search term(s)")
    ap.add_argument("--limit", type=int, default=50, help="API results per query")
    ap.add_argument("--top", type=int, default=3, help="product pages fetched per query")
    ap.add_argument("--fast", action="store_true", help="skip product pages (API only)")
    ap.add_argument("--qty", default="1",
                    help="BOM quantity per query: N or a comma list (default 1)")
    ap.add_argument("--table", action="store_true",
                    help="print a markdown BOM table instead of detail blocks")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", help="append formatted results to a markdown file")
    a = ap.parse_args()

    browser = _Browser()
    results = []
    try:
        for q in a.query:
            try:
                results.append(robu_search(browser, q, a.limit, a.top, a.fast))
            except Exception as e:
                results.append({"query": q, "error": str(e)[:200],
                                "best": None, "candidates": [], "tile_count": 0})
    finally:
        browser.close()

    for r, n in zip(results, _parse_qtys(a.qty, len(results))):
        apply_qty(r, n)

    if a.json:
        print(json.dumps(results if len(results) > 1 else results[0],
                         indent=2, ensure_ascii=False))
        return

    report = _table(results) if a.table else _report(results)
    print(report)
    if a.out:
        with open(a.out, "a", encoding="utf-8") as f:
            f.write("\n\n## Robu.in matches — " + time.strftime("%Y-%m-%d") + "\n\n" + report)


if __name__ == "__main__":
    main()
