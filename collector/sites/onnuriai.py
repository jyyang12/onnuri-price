import html
import re

from ..common import Product, session, to_int, rate, pick_image

SITE = "onnuriai"
SITE_NAME = "꾹AI온누리몰"
HOST = "https://onnuri.ai"
MAX_PAGES = 200


def collect():
    s = session()
    home = s.get(HOST + "/", timeout=40).text
    cats = list(dict.fromkeys(re.findall(r'/category\?k_catecno1=(\d+)"', home)))
    names = {}
    for c, label in re.findall(r'/category\?k_catecno1=(\d+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{1,20})<', home):
        names.setdefault(c, label.strip())
    out, seen = [], set()
    for cat in cats:
        for page in range(1, MAX_PAGES + 1):
            h = s.get(f"{HOST}/category", params={"page": page, "page_num": 20, "k_order": 3, "k_catecno1": cat}, timeout=40).text
            new = 0
            for m in re.finditer(r'<a href="\./product\?[^"]*prdno=(\d+)">(.*?)</a>', h, re.S):
                pid, body = m.group(1), m.group(2)
                if pid in seen:
                    continue
                name = re.search(r'class="pro_title">(.*?)</p>', body, re.S)
                price = re.search(r"<strong>(?:<span[^>]*>\d+%</span>)?\s*([\d,]+)</strong>", body)
                if not name or not price:
                    continue
                seen.add(pid); new += 1
                pct = re.search(r'class="discount">(\d+)%', body)
                orig = re.search(r'class="won">([\d,]+)원', body)
                # 썸네일 앞에 온누리 마크 아이콘이 있어 thumb_wrap 안의 이미지를 집는다
                img = re.search(r'class="thumb_wrap"><img src="([^"]+)"', body)
                img_url = img.group(1) if img else pick_image(body)
                if img_url and not img_url.startswith("http"):
                    img_url = f"{HOST}/{img_url.lstrip('./')}"
                price_v, orig_v = to_int(price.group(1)), to_int(orig.group(1) if orig else None)
                out.append(Product(
                    site=SITE, site_name=SITE_NAME, product_id=pid,
                    name=html.unescape(re.sub(r"<[^>]+>", "", name.group(1))).strip(),
                    price=price_v, orig_price=orig_v if orig_v and orig_v != price_v else None,
                    discount_rate=to_int(pct.group(1)) if pct else rate(price_v, orig_v),
                    benefit="", free_delivery=True if "무료배송" in body else None,
                    url=f"{HOST}/product?prdno={pid}", image=img_url, category=names.get(cat, ""),
                    rating=None, review_count=None, featured="i_hot" in body,
                ))
            if new == 0 or f"page={page + 1}&" not in h:
                break
    return out
