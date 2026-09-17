"""같은 상품을 몰별 판매처(offer)로 묶어 웹에서 쓸 압축 구조를 만든다."""
import re
from collections import Counter, defaultdict

from .brand import extract as extract_brand

TAG = re.compile(r"\[[^\]]*\]")          # [농할], [품질보장] 같은 홍보 말머리
NONWORD = re.compile(r"[^0-9a-z가-힣]")
MIN_KEY = 6
MIN_BRAND_USES = 3


def merge_key(name: str) -> str:
    return NONWORD.sub("", TAG.sub("", (name or "").lower()))


class Prefixes:
    """URL/이미지 주소의 공통 앞부분을 표로 빼서 파일 크기를 줄인다."""

    MIN_USES = 20

    def __init__(self, urls):
        counts = Counter(u[: u.rfind("/") + 1] for u in urls if u and "/" in u)
        self.table = [p for p, c in counts.most_common() if c >= self.MIN_USES and len(p) > 12]
        self.index = {p: i for i, p in enumerate(self.table)}

    def pack(self, url: str):
        i = self.index.get(url[: url.rfind("/") + 1]) if url and "/" in url else None
        return [i, url[url.rfind("/") + 1:]] if i is not None else url


def _offer(p, site_index, pre):
    o = {"s": site_index[p["site"]], "p": p["price"], "u": pre.pack(p["url"])}
    if p.get("orig_price"):
        o["op"] = p["orig_price"]
    if p.get("discount_rate"):
        o["d"] = p["discount_rate"]
    if p.get("benefit"):
        o["b"] = p["benefit"]
    if p.get("free_delivery"):
        o["f"] = 1
    if p.get("rating"):
        o["r"] = p["rating"]
    if p.get("review_count"):
        o["rc"] = p["review_count"]
    if p.get("sales"):
        o["sl"] = p["sales"]
    if p.get("featured"):
        o["ft"] = 1
    return o


def build(collected_at: str, sites: dict, groups: list, products: list) -> dict:
    site_index = {k: i for i, k in enumerate(sites)}
    group_index = {g: i for i, g in enumerate(groups)}

    buckets = defaultdict(list)
    for i, p in enumerate(products):
        if not p.get("name") or not p.get("price"):
            continue
        k = merge_key(p["name"])
        buckets[k if len(k) >= MIN_KEY else f"~{i}"].append(p)

    pre = Prefixes([p.get("url", "") for p in products] + [p.get("image", "") for p in products])

    out = []
    brand_of = {}
    for items in buckets.values():
        names = Counter(p["name"].strip() for p in items)
        top = max(names.values())
        name = min((n for n, c in names.items() if c == top), key=len)
        entry = {"n": name, "g": group_index.get(items[0]["group"], group_index.get("기타", 0))}
        # 묶음 안 어느 몰에서든 브랜드를 찾으면 쓴다
        b = next((x for x in (extract_brand(p["name"]) for p in items) if x), "")
        if b:
            brand_of[id(entry)] = b
        img = next((p["image"] for p in items if p.get("image")), "")
        if img:
            entry["i"] = pre.pack(img)
        entry["o"] = sorted((_offer(p, site_index, pre) for p in items), key=lambda o: o["p"])
        out.append(entry)

    counts = Counter(brand_of.values())
    brands = [b for b, c in counts.most_common() if c >= MIN_BRAND_USES]
    brand_index = {b: i for i, b in enumerate(brands)}
    for entry in out:
        i = brand_index.get(brand_of.get(id(entry), ""))
        if i is not None:
            entry["br"] = i

    out.sort(key=lambda e: -len(e["o"]))
    return {
        "t": collected_at,
        "s": [{"k": k, "n": v["site_name"], "c": v["count"]} for k, v in sites.items()],
        "g": groups,
        "b": brands,
        "x": pre.table,
        "p": out,
    }
