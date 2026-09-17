import json
import re

from ..common import Product, session, to_int, to_float, rate

SITE = "hmall"
SITE_NAME = "현대홈쇼핑 온누리샵"
ROOT_SECT = 3132118
BASE = "https://www.hmall.com/md/dpa/searchSpexSectItem"
IMG_BASE = "https://image.hmall.com/static/"


def _next_data(page: str) -> dict:
    m = re.search(r'id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
    return json.loads(m.group(1))["props"]["pageProps"]


def _walk_items(obj, category, found: dict):
    if isinstance(obj, dict):
        if "slitmCd" in obj and "slitmNm" in obj and "sellPrc" in obj:
            found.setdefault(obj["slitmCd"], (obj, category))
            return
        cat = obj.get("spexSectNm") or obj.get("sectNm") or category
        for v in obj.values():
            _walk_items(v, cat, found)
    elif isinstance(obj, list):
        for v in obj:
            _walk_items(v, category, found)


def _image(it: dict) -> str:
    cd = str(it.get("slitmCd") or "")
    name = it.get("itemBaseImgNm") or f"{cd}_0.jpg"
    if name.startswith("http"):
        return name
    if len(cd) < 8:
        return ""
    # image.hmall.com 경로는 상품코드 자릿수를 재배열해 만든다 (예: 2252244962 -> 9/4/24/52)
    return f"{IMG_BASE}{cd[7]}/{cd[6]}/{cd[4:6]}/{cd[2:4]}/{name}?RS=300x300"


def collect():
    s = session()
    found = {}
    root = _next_data(s.get(BASE, params={"sectId": ROOT_SECT}, timeout=30).text)
    data = root.get("data", {})
    _walk_items(data, "", found)
    sections = data.get("holiInfo", {}).get("coinAnchorList", [])
    for sect in sections:
        sid, sname = sect.get("spexSectId"), sect.get("spexSectNm", "")
        if not sid:
            continue
        try:
            pp = _next_data(s.get(BASE, params={"sectId": sid}, timeout=30).text)
        except Exception:
            continue
        _walk_items(pp.get("data") or pp, sname, found)

    out = []
    for cd, (it, cat) in found.items():
        sell = to_int(it.get("sellPrc"))
        final = to_int(it.get("bbprc")) or sell
        benefit = []
        if to_int(it.get("copnDcAmt")):
            benefit.append(f"쿠폰 {it['copnDcAmt']:,}원")
        if to_int(it.get("copnDcRate")):
            benefit.append(f"쿠폰 {it['copnDcRate']}%")
        if to_int(it.get("dcSvmt")):
            benefit.append(f"적립 {it['dcSvmt']:,}")
        dlvc = to_int(it.get("dlvcBasicAmt"))
        out.append(Product(
            site=SITE, site_name=SITE_NAME,
            product_id=str(cd),
            name=(it.get("slitmNm") or "").strip(),
            price=final,
            orig_price=sell if sell and sell != final else None,
            discount_rate=to_int(it.get("dcRate")) or rate(final, sell),
            benefit=" / ".join(benefit),
            free_delivery=(dlvc == 0) if dlvc is not None else None,
            url=f"https://www.hmall.com/md/pda/itemPtc?slitmCd={cd}",
            image=_image(it),
            category=cat or "",
            rating=to_float(it.get("itemEvalScrg")) or None,
            review_count=to_int(it.get("itemStsfTotCnt")),
        ))
    return out
