import html
import re

from ..common import Product, session, to_int, rate

SITE = "onnuri5"
SITE_NAME = "온누리5일장"
HOST = "https://www.onnuri5.com"
MAX_PAGES = 100


def collect():
    s = session()
    home = s.get(HOST + "/", timeout=(20, 120)).text  # 응답이 매우 느린 사이트
    cats = list(dict.fromkeys(re.findall(r'/shop/goods_list\?cno=(\d+)"', home)))
    names = {}
    for c, label in re.findall(r'/shop/goods_list\?cno=(\d+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{1,20})<', home):
        names.setdefault(c, label.strip())
    out, seen = [], set()
    for cat in cats:
        for page in range(1, MAX_PAGES + 1):
            try:
                h = s.get(f"{HOST}/shop/goods_list", params={"cno": cat, "page": page}, timeout=60).text
            except Exception:
                break
            new = 0
            for m in re.finditer(r'<div class="product">(.*?)<div class="icon_list">(.*?)</div>', h, re.S):
                body, icons = m.group(1), m.group(2)
                pid = re.search(r"goods_detail\?hash=(\w+)", body)
                name = re.search(r'class="item_tit">(.*?)</a>', body, re.S)
                if not pid or not name or pid.group(1) in seen:
                    continue
                seen.add(pid.group(1)); new += 1
                normal = re.search(r'class="prc_normal">([\d,]+)', body)
                sell = re.search(r'class="prc_sell_prc">\s*([\d,]+)', body)
                pct = re.search(r'class="prc_sale_per">(\d+)', body)
                img = re.search(r'<img src="([^"]+)"', body)
                sell_v = to_int(sell.group(1) if sell else None) or to_int(normal.group(1) if normal else None)
                normal_v = to_int(normal.group(1) if normal else None)
                out.append(Product(
                    site=SITE, site_name=SITE_NAME, product_id=pid.group(1),
                    name=html.unescape(re.sub(r"<[^>]+>", "", name.group(1))).strip(),
                    price=sell_v, orig_price=normal_v if normal_v and normal_v != sell_v else None,
                    discount_rate=to_int(pct.group(1)) if pct else rate(sell_v, normal_v), benefit="",
                    free_delivery=True if "무료배송" in icons else None,
                    url=f"{HOST}/shop/goods_detail?hash={pid.group(1)}", image=img.group(1) if img else "",
                    category=names.get(cat, ""), rating=None, review_count=None,
                ))
            if new == 0 or f"cno={cat}&page={page + 1}" not in h:
                break
    return out
