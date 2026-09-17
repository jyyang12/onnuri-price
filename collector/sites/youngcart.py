"""영카트(그누보드) 기반 몰: 온누리공공몰, 온누리마켓."""
import html
import re

from ..common import Product, session, to_int, to_float, rate, pick_image

MAX_PAGES = 100
MAX_PAGES_TOTAL = 300  # 개인용이라 상위 카테고리 위주로 적당히 끊는다


def _text(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()


def _collect(site, site_name, host, cat_filter, paged):
    total_pages = 0
    s = session()
    home = s.get(host + "/", timeout=30).text
    cats = [c for c in dict.fromkeys(re.findall(r"/shop/list\.php\?ca_id=(\d+)", home)) if cat_filter(c)]
    names = {}
    for c, label in re.findall(r'/shop/list\.php\?ca_id=(\d+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{1,30})<', home):
        names.setdefault(c, label.strip())
    out, seen = [], set()
    for cat in cats:
        for page in range(1, (MAX_PAGES if paged else 1) + 1):
            if total_pages >= MAX_PAGES_TOTAL:
                return out
            total_pages += 1
            try:
                h = s.get(f"{host}/shop/list.php", params={"ca_id": cat, "page": page}, timeout=60).text
            except Exception:
                break
            new = 0
            for m in re.finditer(r'<a href="([^"]*item\.php\?it_id=(\w+)[^"]*)"', h):
                pid = m.group(2)
                if pid in seen:
                    continue
                # 이미지 링크와 상품명 링크가 같은 it_id로 두 번 나오므로 첫 링크부터 넉넉히 잘라 한 번에 파싱.
                # 주석 안에 아이콘 <img>가 들어 있어 제거하지 않으면 상품 이미지 대신 그것이 잡힌다.
                body = re.sub(r"<!--.*?-->", "", h[m.start(): m.start() + 6000], flags=re.S)
                name = re.search(r'class="[^"]*cut2[^"]*">([^<]+)<', body) or re.search(r'alt="([^"]+)"', body)
                if not name:
                    continue
                seen.add(pid); new += 1
                img = pick_image(body)
                price = re.search(r'(?:p-discount|main_list_price_li2)[^>]*>\s*([\d,]+)원', body)
                orig = re.search(r"<strike>([\d,]+)원", body)
                dc = re.search(r"main_list_price_li1[^>]*>(\d+)%", body)
                coupon = re.search(r"쿠폰</span>.{0,80}?(\d+)%", body, re.S)
                star = re.search(r"s_star(\d+)\.png", body)
                reviews = re.search(r'main_list_star_cnt[^>]*>\((\d+)\)', body) or re.search(r'nl-rate.{0,1500}?<span>\((\d+)\)</span>', body, re.S)
                price_v, orig_v = to_int(price.group(1) if price else None), to_int(orig.group(1) if orig else None)
                out.append(Product(
                    site=site, site_name=site_name, product_id=pid,
                    name=html.unescape(name.group(1)).strip(),
                    price=price_v, orig_price=orig_v if orig_v and orig_v != price_v else None,
                    discount_rate=to_int(dc.group(1)) if dc else rate(price_v, orig_v),
                    benefit=f"쿠폰 {coupon.group(1)}%" if coupon else "",
                    free_delivery=True if "무료배송" in body else None,
                    url=html.unescape(m.group(1)) if m.group(1).startswith("http") else host + "/shop/" + html.unescape(m.group(1)).lstrip("./"),
                    image=img, category=names.get(cat, ""),
                    rating=to_float(star.group(1)) if star else None,
                    review_count=to_int(reviews.group(1)) if reviews else None,
                ))
            if new == 0 or f"page={page + 1}" not in h:
                break
    return out
