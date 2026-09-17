import html
import re

from ..common import Product, session, to_int, to_float

SITE = "11st"
SITE_NAME = "11번가 온누리마켓"
EXHIBITION = 2210481
DETAIL = f"https://plan.11st.co.kr/plan/front/exhibitions/{EXHIBITION}/detail"


def _themes(page: str):
    names = {}
    for no, name in re.findall(r"content_no&quot;:&quot;(\d+)&quot;,&quot;content_name&quot;:&quot;([^&]+)", page):
        names[no] = html.unescape(name)
    themes = []
    for idx, theme_no in re.findall(r'name="themeNo_(\d+)" value="(\d+)"', page):
        def val(key):
            m = re.search(rf'name="{key}_{idx}" value="([^"]*)"', page)
            return m.group(1) if m else ""
        themes.append({
            "index": int(idx),
            "themeNo": theme_no,
            "templateType": val("templateType"),
            "count": val("countOfProducts") or "100",
            "sort": val("productSortCode") or "02",
            "name": names.get(theme_no, ""),
        })
    return themes


def _benefit(p: dict) -> str:
    parts = []
    b = p.get("benefit") or {}
    if isinstance(b, dict):
        if b.get("pntRsvRt"):
            parts.append(f"{b['pntRsvRt']} 적립")
        if to_int(b.get("dscCardRt")):
            parts.append(f"카드 {b['dscCardRt']}% 할인")
        if b.get("etcBenefit"):
            parts.append(b["etcBenefit"])
    flag = p.get("promotionFlagInfo")
    if isinstance(flag, str) and flag:
        # 목록 API는 <dd><span>~7% 적립</span></dd> 같은 HTML 조각으로 내려준다
        parts += [t.strip() for t in re.findall(r">([^<>]+)<", flag) if t.strip()]
    elif isinstance(flag, list):
        parts += [f.get("promotionGroupName", "") for f in flag if f.get("promotionGroupName")]
    return " / ".join(dict.fromkeys(parts))


def collect():
    s = session()
    page = s.get(DETAIL, timeout=30).text
    themes = _themes(page)
    out = []
    for t in themes:
        r = s.post(
            f"https://plan.11st.co.kr/plan/front/exhibitions/{EXHIBITION}/themes/{t['themeNo']}/products",
            data={
                "templateType": t["templateType"],
                "page": 0,
                "size": t["count"],
                "themeIndex": t["index"],
                "productSortCode": t["sort"],
                "deliveryType": "",
                "isUsableProductNetFunnel": "false",
                "recommendedProducts": "",
                "recommendRequestId": "",
                "isAcme": "false",
            },
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": DETAIL},
            timeout=30,
        )
        for p in r.json().get("themeProducts", []):
            price = to_int(p.get("finalPrice"))
            orig = to_int(p.get("sellPrice"))
            delivery = p.get("deliveryInfo") or ""
            out.append(Product(
                site=SITE, site_name=SITE_NAME,
                product_id=str(p.get("productNo")),
                name=p.get("productName", "").strip(),
                price=price,
                orig_price=orig if orig and orig != price else None,
                discount_rate=to_int(p.get("discountRate")) or None,
                benefit=_benefit(p),
                free_delivery=("무료" in delivery) if delivery else None,
                url=p.get("productLink", ""),
                image=p.get("productImage", ""),
                category=t["name"],
                rating=to_float(p.get("satisfactionScore")),
                review_count=to_int(p.get("reviewCount")),
            ))
    return out
