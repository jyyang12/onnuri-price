import re

from ..common import Product, session, to_int, to_float, rate

SITE = "lotteon"
SITE_NAME = "롯데ON 온누리상생스토어"
SHOP_NO = 57821
PBF = "https://pbf.lotteon.com"
MALL_NO = 1
ROWS = 100


def _get(s, url, **params):
    r = s.get(url, params=params, headers={"Accept": "application/json", "Referer": "https://www.lotteon.com/"}, timeout=30)
    r.raise_for_status()
    return r.json().get("data") or {}


def _price(p: dict):
    candidates = [to_int(p.get(k)) for k in ("frstFvrPrc", "scndFvrPrc", "onerFvrPrc", "dcAplyTotAmt")]
    candidates = [c for c in candidates if c]
    sl = to_int(p.get("slPrc"))
    price = min(candidates) if candidates else sl
    return price, sl


def collect():
    s = session()
    shop = s.get(f"{PBF}/display/v2/dpShop/seltMainShop", params={"dshopNo": SHOP_NO, "mdiaCd": "PC"},
                 headers={"Accept": "application/json", "Referer": "https://www.lotteon.com/"}, timeout=30).text
    plan_ids = list(dict.fromkeys(re.findall(r"planDetail/(\d+)", shop)))

    out, seen = [], set()
    for spdp in plan_ids:
        try:
            plan = _get(s, f"{PBF}/display/v2/plan/seltSpecialDisplayPlanV2", spdpNo=spdp, mdiaCd="PC")
            sects = _get(s, f"{PBF}/display/v2/plan/seltPlanSctnListV2", spdpNo=spdp, mallNo=MALL_NO, mdiaCd="PC")
        except Exception:
            continue
        plan_name = plan.get("spdpNm", "")
        for sect in sects.get("sctnDetail", []):
            sctn_no, sctn_nm = sect.get("sctnNo"), sect.get("sctnNm", "")
            page = 1
            while True:
                try:
                    d = _get(s, f"{PBF}/display/o/v2/plan/seltPlanProductListV2",
                             spdpNo=spdp, sctnNo=sctn_no, mallNo=MALL_NO, mdiaCd="PC", pageNo=page, rowsPerPage=ROWS)
                except Exception:
                    break
                pl = d.get("planPdList") or {}
                rows = pl.get("dataList") or []
                for p in rows:
                    pid = p.get("spdNo")
                    if not pid or pid in seen:
                        continue
                    seen.add(pid)
                    price, sl = _price(p)
                    benefit = []
                    if to_int(p.get("onerDcRt")):
                        benefit.append(f"할인 {p['onerDcRt']}%")
                    if p.get("isQuantityDcPromotion"):
                        benefit.append("수량할인")
                    sitm = p.get("sitmNo")
                    url = f"https://www.lotteon.com/p/product/{pid}" + (f"?sitmNo={sitm}" if sitm else "")
                    out.append(Product(
                        site=SITE, site_name=SITE_NAME,
                        product_id=pid,
                        name=(p.get("spdNm") or "").strip(),
                        price=price,
                        orig_price=sl if sl and sl != price else None,
                        discount_rate=rate(price, sl),
                        benefit=" / ".join(benefit),
                        free_delivery=None,
                        url=url,
                        image=p.get("imgFullUrl", ""),
                        category=f"{plan_name} > {sctn_nm}".strip(" >"),
                        rating=to_float(p.get("avgRvwGrd") or p.get("rvwAvgScr")),
                        review_count=to_int(p.get("rvwCnt")),
                        sales=to_int(p.get("mmSlQty")),
                    ))
                total = to_int(pl.get("totalCount")) or 0
                if page * ROWS >= total or not rows:
                    break
                page += 1
    return out
