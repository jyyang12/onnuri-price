import html
import re

from ..common import Product, session, to_int, rate

SITE = "onnurimall"
SITE_NAME = "온누리시장"
HOST = "https://www.onnuri-mall.co.kr"
PAGE_SIZE = 40
MAX_PAGES = 60

BLOCK = re.compile(r'fn\.goDetail\(&quot;(\d+)&quot;, (\d+)\);" class="imgBox">(.*?)(?=fn\.goDetail\(&quot;\d+&quot;, \d+\);" class="imgBox">|$)', re.S)


def _text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def collect():
    s = session()
    home = s.get(HOST + "/", timeout=30).text
    cats = list(dict.fromkeys(re.findall(r"/product/list\?dispCatNo=(\d+)", home)))
    out, seen = [], set()
    for cat in cats:
        for page in range(1, MAX_PAGES + 1):
            try:
                r = s.post(f"{HOST}/product/listAjax", params={"pageNum": page, "pageSize": PAGE_SIZE},
                           json={"dispCatNo": cat, "pageNum": page, "pageSize": PAGE_SIZE, "orderByType": ""},
                           headers={"Referer": f"{HOST}/product/list?dispCatNo={cat}", "X-Requested-With": "XMLHttpRequest"}, timeout=40)
            except Exception:
                break
            new = 0
            for m in BLOCK.finditer(r.text):
                pid, disp, body = m.group(1), m.group(2), m.group(3)
                if pid in seen:
                    continue
                seen.add(pid); new += 1
                name = re.search(r'<p class="text">(.*?)</p>', body, re.S)
                orig = re.search(r'line-through;">([\d,]+)', body)
                price = re.search(r'<span class="money">([\d,]+)원', body)
                img = re.search(r"background-image:url\(([^)]+)\)", body)
                price_v, orig_v = to_int(price.group(1) if price else None), to_int(orig.group(1) if orig else None)
                out.append(Product(
                    site=SITE, site_name=SITE_NAME, product_id=pid,
                    name=_text(name.group(1)) if name else "",
                    price=price_v, orig_price=orig_v if orig_v and orig_v != price_v else None,
                    discount_rate=rate(price_v, orig_v), benefit="",
                    free_delivery=True if re.search(r">\s*무료배송\s*<", body) else None,  # 주석에도 '무료배송'이 있어 태그 텍스트만 확인
                    url=f"{HOST}/product/detail?prodNo={pid}&dispCatNo={disp}",
                    image=img.group(1).strip("'\"") if img else "", category="",
                    rating=None, review_count=None,
                ))
            if new == 0:
                break
    return out
