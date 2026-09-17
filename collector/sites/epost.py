import html
import re

from ..common import Product, session, to_int, rate

SITE = "epost"
SITE_NAME = "우체국쇼핑 전통시장"
HOST = "https://mall.epost.go.kr"
LIST = f"{HOST}/fo/pavln/sijangAll.do"
PAGE_UNIT = 100
MAX_PAGES = 200

BLOCK = re.compile(r"""fn_goodsDetailView\('(\w+)','(\w*)','(\w*)','(\w*)','(\w*)'\);">(.*?)</a>""", re.S)


def collect():
    s = session()
    s.get(LIST, timeout=40)  # 세션 쿠키가 있어야 pageIndex가 적용됨
    out, seen = [], set()
    for page in range(1, MAX_PAGES + 1):
        r = s.post(LIST, data={"pageIndex": page, "pageUnit": PAGE_UNIT, "orderKey": "tp", "listType": "imglist",
                               "searchMCtgryCd": "99", "searchSCtgryCd": "", "srchGoodsNm": "", "areaCd": "000"},
                   headers={"Referer": LIST}, timeout=60)
        new = 0
        for m in BLOCK.finditer(r.text):
            gid, body = m.group(1), m.group(6)
            if gid in seen:
                continue
            name = re.search(r'class="(?:top_title|tit)">\s*(.*?)\s*</p>', body, re.S)
            if not name:
                continue
            seen.add(gid); new += 1
            cost = re.search(r'class="cost"><span><em>([\d,]+)</em>', body) or re.search(r'판매가</span>\s*<span><em>([\d,]+)</em>', body)
            dc = re.search(r'class="dc"><span><em>([\d,]+)</em>', body)
            pct = re.search(r'class="sale_point[^"]*">.*?<em>(\d+)</em>', body, re.S) or re.search(r'class="per">(\d+)%', body)
            img = re.search(r'<img src="([^"]+)"', body)
            star = re.search(r'class="star(\d+)"', body)
            gun = re.search(r'class="gun">(\d+)건', body)
            price_v, orig_v = to_int(cost.group(1) if cost else None), to_int(dc.group(1) if dc else None)
            out.append(Product(
                site=SITE, site_name=SITE_NAME, product_id=gid,
                name=html.unescape(re.sub(r"<[^>]+>", "", name.group(1))).strip(),
                price=price_v, orig_price=orig_v if orig_v and orig_v != price_v else None,
                discount_rate=to_int(pct.group(1)) if pct else rate(price_v, orig_v), benefit="",
                free_delivery=True if "무료배송" in body else None,
                url=f"{HOST}/fo/goods/goodsDetailView.do?goodsCd={gid}",
                image=img.group(1) if img else "", category="",
                rating=(int(star.group(1)) / 2) if star else None, review_count=to_int(gun.group(1)) if gun else None,
            ))
        if new == 0:
            break
    return out
