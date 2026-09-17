import json
import re
from urllib.parse import unquote

from ..common import Product, session, to_int, to_float, rate

SITE = "onnurideal"
SITE_NAME = "온누리핫딜"
HOST = "https://onnurideal.com"
MAX_PAGES = 100


def _products(page_html: str):
    h = page_html.replace('\\"', '"')
    i = h.find('"initialPage":{"products":[')
    if i < 0:
        return [], 1
    start = h.find("[", i)
    try:
        arr, end = json.JSONDecoder().raw_decode(h, start)
    except ValueError:
        return [], 1
    tp = re.search(r'"totalPages":(\d+)', h[end:end + 300])
    return arr, int(tp.group(1)) if tp else 1


def collect():
    s = session()
    home = s.get(HOST + "/", timeout=40).text
    cats = list(dict.fromkeys(re.findall(r'/category\?category=([^"&]+)', home)))
    out, seen = [], set()
    for cat in cats:
        cat_name = unquote(cat)
        page, total = 1, 1
        while page <= total and page <= MAX_PAGES:
            h = s.get(f"{HOST}/category", params={"category": cat_name, "page": page}, timeout=40).text
            arr, total = _products(h)
            if not arr:
                break
            for p in arr:
                pid = p.get("routeCode") or p.get("productCode")
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                price, orig = to_int(p.get("price")), to_int(p.get("originalPrice"))
                labels = p.get("benefitLabels") or []
                out.append(Product(
                    site=SITE, site_name=SITE_NAME, product_id=pid, name=(p.get("name") or "").strip(),
                    price=price, orig_price=orig if orig and orig != price else None,
                    discount_rate=to_int(p.get("discountRate")) or rate(price, orig),
                    benefit=" / ".join(str(x) for x in labels if x),
                    free_delivery=bool(p.get("isFreeShipping")) or None,
                    url=f"{HOST}/products/{pid}", image=p.get("image") or "",
                    category=cat_name + (f" · {p['marketName']}" if p.get("marketName") else ""),
                    rating=to_float(p.get("rating")) or None, review_count=to_int(p.get("reviewCount")) or None,
                    featured=bool(p.get("isBest")),
                ))
            page += 1
    return out
