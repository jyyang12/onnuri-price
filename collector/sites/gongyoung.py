import re
import xml.etree.ElementTree as ET

from ..common import Product, session, to_int, to_float, rate

SITE = "gongyoung"
SITE_NAME = "공영쇼핑 디지털온누리샵"
EBT_NO = 4328
HOST = "https://www.gongyoungshop.kr"
DETAIL = f"{HOST}/exhibition/ebtDetail.do?ebtNo={EBT_NO}"
IMG_BASE = "https://img.publichs.com/ECMCFO/share/product"
BATCH = 50


def _text(el, tag):
    node = el.find(tag)
    return node.text if node is not None and node.text else ""


def collect():
    s = session()
    hdr = {"X-Requested-With": "XMLHttpRequest", "Referer": DETAIL}
    raw = s.post(f"{HOST}/exhibition/getEbtDetail.do", data={"ebtNo": EBT_NO}, headers=hdr, timeout=60).text
    ids = list(dict.fromkeys(re.findall(r"<prdId>(\d+)</prdId>", raw)))

    out = []
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i + BATCH]
        r = s.post(
            f"{HOST}/goods/getGoodsUnitInfo.do",
            json={"prdInfoList": [{"prdId": pid} for pid in chunk]},
            headers=hdr, timeout=60,
        )
        root = ET.fromstring(r.text)
        for el in root.iter("goodsUnitInfoList"):
            pid = _text(el, "prdId")
            if not pid:
                continue
            base = to_int(_text(el, "prdPrc"))
            dc = to_int(_text(el, "pnmDcRate")) or 0
            price = round(base * (100 - dc) / 100) if base and dc else base
            benefit = []
            if dc:
                benefit.append(f"즉시할인 {dc}%")
            card = to_int(_text(el, "dcCardRt"))
            if card:
                benefit.append(f"{_text(el, 'dcCardNm')} 카드 {card}%")
            img = _text(el, "imgUrl")
            out.append(Product(
                site=SITE, site_name=SITE_NAME,
                product_id=pid,
                name=_text(el, "prdNm").strip(),
                price=price,
                orig_price=base if base and base != price else None,
                discount_rate=rate(price, base),
                benefit=" / ".join(benefit),
                free_delivery=(_text(el, "freeDlvYn") == "Y") or None,
                url=f"{HOST}/goods/selectGoodsDetail.do?prdId={pid}",
                image=(IMG_BASE + img) if img.startswith("/") else img,
                category=_text(el, "dispCatNm"),
                rating=to_float(_text(el, "avgValFive")) or None,
                review_count=to_int(_text(el, "assmtCnt")),
                sales=to_int(_text(el, "ordQty")),
            ))
    return out
