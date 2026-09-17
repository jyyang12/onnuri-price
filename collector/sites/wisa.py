"""위사(WISA) 솔루션 기반 몰: 온누리굿데이, 인더마켓온누리몰, 온누리 찬스."""
import html
import re

from ..common import Product, session, to_int, to_float, rate, pick_image

MAX_PAGES_PER_CAT = 80
MAX_PAGES_TOTAL = 800


def _text(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()


def _parse_item_box(pcode, body):
    name = re.search(r'class="item_name"[^>]*>(.*?)</a>', body, re.S) or re.search(r'alt="([^"]+)"', body)
    before = re.search(r'class="before">.*?class="won">([\d,]+)', body, re.S)
    after = re.search(r'class="after">.*?class="won">([\d,]+)', body, re.S)
    pct = re.search(r'class="percent">(\d+)%', body)
    # 썸네일 앞에 프로모션 배지 <img>가 오는 경우가 있어 상품 이미지 영역을 먼저 찾는다
    img = re.search(r'class="(?:ov_img|img)"><img src="([^"]+)"', body)
    coupon = re.search(r'class="coupon_line">([^<]+)<', body)
    reviews = re.search(r'class="num">\((\d+)\)', body)
    return dict(name=_text(name.group(1)) if name else "", price=to_int(after.group(1) if after else None),
                orig=to_int(before.group(1) if before else None), pct=to_int(pct.group(1)) if pct else None,
                img=img.group(1) if img else pick_image(body), benefit=coupon.group(1).strip() if coupon else "",
                reviews=to_int(reviews.group(1)) if reviews else None, market="")


def _parse_card(pcode, body):
    name = re.search(r'data-product-name="([^"]*)"', body)
    price = re.search(r'data-product-price="(\d+)"', body)
    orig = re.search(r'class="ori-price">([\d,]+)', body)
    pct = re.search(r'class="dc-rate">(\d+)%', body)
    img = re.search(r'class="img-wrapper">.*?<img src="([^"]+)"', body, re.S)
    market = re.search(r'class="market-info">\s*([^<]+?)\s*<', body)
    return dict(name=html.unescape(name.group(1)) if name else "", price=to_int(price.group(1) if price else None),
                orig=to_int(orig.group(1) if orig else None), pct=to_int(pct.group(1)) if pct else None,
                img=img.group(1) if img else pick_image(body), benefit="", reviews=None,
                market=market.group(1).strip() if market else "")


def _collect(site, site_name, host):
    s = session()
    home = s.get(host + "/", timeout=40).text
    cats = list(dict.fromkeys(re.findall(r"pn=product\.list&(?:amp;)?cuid=(\d+)", home)))
    names = {}
    for c, label in re.findall(r'pn=product\.list&(?:amp;)?cuid=(\d+)"[^>]*>\s*([^<\t\n]{1,30})<', home):
        names.setdefault(c, label.strip())
    out, seen, total_pages = [], set(), 0
    for cat in cats:
        for page in range(1, MAX_PAGES_PER_CAT + 1):
            if total_pages >= MAX_PAGES_TOTAL:
                return out
            h = s.get(host + "/", params={"pn": "product.list", "cuid": cat, "listpg": page}, timeout=40).text
            total_pages += 1
            new = 0
            for m in re.finditer(r'(?:data-pcode|data-product-id)="([\w-]+)"', h):
                pcode = m.group(1)
                if pcode in seen:
                    continue
                body = h[m.start(): m.start() + 5000]
                d = _parse_card(pcode, body) if "product-card" in body[:300] else _parse_item_box(pcode, body)
                if not d["name"] or not d["price"]:
                    continue
                seen.add(pcode); new += 1
                img = d["img"]
                if img.startswith("//"):
                    img = "https:" + img
                elif img.startswith("/"):
                    img = host + img
                out.append(Product(
                    site=site, site_name=site_name, product_id=pcode, name=d["name"],
                    price=d["price"], orig_price=d["orig"] if d["orig"] and d["orig"] != d["price"] else None,
                    discount_rate=d["pct"] or rate(d["price"], d["orig"]), benefit=d["benefit"],
                    free_delivery=True if "무료배송" in body else None,
                    url=f"{host}/?pn=product.view&pcode={pcode}", image=img,
                    category=names.get(cat, "") + (f" · {d['market']}" if d["market"] else ""),
                    rating=None, review_count=d["reviews"],
                ))
            if new == 0 or f"listpg={page + 1}" not in h:
                break
    return out
