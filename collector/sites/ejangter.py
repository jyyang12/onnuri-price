import html
import re

from ..common import Product, session, to_int, rate

SITE = "ejangter"
SITE_NAME = "온누리팔도시장"
HOST = "https://e-jangter.com"
MAX_PAGES = 100


def collect():
    s = session()
    home = s.get(f"{HOST}/Extmall/Onnuri.aspx", timeout=40).text
    cats = list(dict.fromkeys(re.findall(r"/Goods/SubMain\.aspx\?cate=(\d+)", home)))
    names = {}
    for c, label in re.findall(r'/Goods/SubMain\.aspx\?cate=(\d+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{1,20})<', home):
        names.setdefault(c, label.strip())
    out, seen = [], set()
    for cat in cats:
        for page in range(1, MAX_PAGES + 1):
            h = s.get(f"{HOST}/Goods/SubMain.aspx", params={"cate": cat, "page": page}, timeout=40).text
            new = 0
            for m in re.finditer(r'<div class="item_box">(.*?)</div>\s*</li>', h, re.S):
                body = m.group(1)
                pid = re.search(r"guid=(\d+)", body)
                name = re.search(r'class="item_n">(.*?)</div>', body, re.S)
                price = re.search(r'class="item_price_n"><span>([\d,]+)</span>', body)
                if not pid or not name or not price or pid.group(1) in seen:
                    continue
                seen.add(pid.group(1)); new += 1
                pct = re.search(r'class="item_price_sale"><span>(\d+)</span>', body)
                img = re.search(r'<img src="([^"]+)"', body)
                img_url = img.group(1) if img else ""
                if img_url.startswith("/"):
                    img_url = HOST + img_url
                price_v = to_int(price.group(1))
                pct_v = to_int(pct.group(1)) if pct else None
                orig_v = round(price_v / (1 - pct_v / 100)) if pct_v and price_v else None
                out.append(Product(
                    site=SITE, site_name=SITE_NAME, product_id=pid.group(1),
                    name=html.unescape(re.sub(r"<[^>]+>", "", name.group(1))).strip(),
                    price=price_v, orig_price=orig_v, discount_rate=pct_v, benefit="",
                    free_delivery=True if "무료배송" in body else None,
                    url=f"{HOST}/Goods/Content.aspx?guid={pid.group(1)}&cate={cat}", image=img_url,
                    category=names.get(cat, ""), rating=None, review_count=None,
                ))
            if new == 0:
                break
    return out
