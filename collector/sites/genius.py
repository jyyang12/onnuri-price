import html
import re

from ..common import Product, session, to_int, rate

SITE = "genius"
SITE_NAME = "지니어스몰"
HOST = "https://luxurysystem.co.kr"
PAGE_SIZE = 12

ITEM_RE = re.compile(
    r'<li>\s*<a href="/product/product\.html\?category=(?P<cat>\d*)&amp;id=(?P<id>\d+)&amp;mode=view[^"]*">'
    r'.*?<img src="(?P<img>[^"]*)".*?<em>(?P<name>.*?)</em>.*?'
    r'<span class="price">(?P<prices>.*?)</span>(?P<rest>.*?)</a>',
    re.S,
)


def _home(s):
    page = s.get(HOST + "/", timeout=30).text
    cats = sorted(set(re.findall(r'product\.html\?category=(\d+)"', page)))
    featured = set(re.findall(r'product\.html\?category=\d*&(?:amp;)?id=(\d+)&(?:amp;)?mode=view', page))
    return cats, featured


def _category_name(page: str) -> str:
    m = re.search(r"이전카테고리</a>([^<]+)</p>", page)
    return html.unescape(m.group(1)).strip() if m else ""


def _parse(page: str, cat_name: str, seen: set, out: list):
    for m in ITEM_RE.finditer(page):
        pid = m.group("id")
        if pid in seen:
            continue
        seen.add(pid)
        prices = [to_int(x) for x in re.findall(r"<i>([^<]*)</i>", m.group("prices"))]
        prices = [p for p in prices if p]
        if not prices:
            continue
        price = min(prices)
        orig = max(prices) if len(prices) > 1 and max(prices) != price else None
        img = m.group("img")
        out.append(Product(
            site=SITE, site_name=SITE_NAME,
            product_id=pid,
            name=html.unescape(re.sub(r"<[^>]+>", "", m.group("name"))).strip(),
            price=price,
            orig_price=orig,
            discount_rate=rate(price, orig),
            benefit="",
            free_delivery=None,
            url=f"{HOST}/product/product.html?category={m.group('cat')}&id={pid}&mode=view",
            image=(HOST + img) if img.startswith("/") else img,
            category=cat_name,
            rating=None,
            review_count=None,
        ))


def collect():
    s = session()
    out, seen = [], set()
    cats, featured = _home(s)
    for code in cats:
        start, name = 0, ""
        while True:
            try:
                r = s.get(f"{HOST}/product/product.html", params={"category": code, "start": start}, timeout=30)
            except Exception:
                break
            name = name or _category_name(r.text)
            before = len(out)
            _parse(r.text, name, seen, out)
            start += PAGE_SIZE
            has_next = re.search(rf"[?&](?:amp;)?start={start}'", r.text) is not None
            if len(out) == before or not has_next:
                break
    for p in out:
        p.featured = p.product_id in featured
    return out
