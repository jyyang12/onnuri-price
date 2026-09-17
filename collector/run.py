import argparse
import gzip
import json
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from .merge import build
from .sites import SITES
from .taxonomy import classify, GROUPS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="온누리 온라인몰 상품 수집기")
    ap.add_argument("--site", action="append", choices=list(SITES), help="특정 사이트만 (여러 번 지정 가능)")
    ap.add_argument("--reclassify", action="store_true", help="수집 없이 기존 데이터의 통합 카테고리만 다시 계산")
    ap.add_argument("--workers", type=int, default=6, help="동시에 수집할 사이트 수")
    args = ap.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    if args.reclassify:
        existing = _load_doc()
        for p in existing["products"]:
            p["group"] = classify(p.get("category", ""), p.get("name", ""))
        existing["groups"] = GROUPS
        counts = Counter(p["site"] for p in existing["products"])
        existing["sites"] = {k: {**existing.get("sites", {}).get(k, {}), "site_name": SITES[k].SITE_NAME,
                                 "count": counts[k]} for k in SITES if counts[k]}
        _save(existing)
        print(f"{len(existing['products'])}개 재분류 완료", file=sys.stderr)
        return

    targets = args.site or list(SITES)
    previous = _load_doc()
    prev_by_site = defaultdict(list)
    for p in previous.get("products", []):
        prev_by_site[p["site"]].append(p)
    products, meta = [], {}

    def run_site(key):
        mod = SITES[key]
        t0 = time.time()
        try:
            items = mod.collect()
            status = "ok"
        except Exception as e:
            items, status = [], f"error: {e!r}"
        for p in items:
            p.group = classify(p.category, p.name)
        info = {"site_name": mod.SITE_NAME, "count": len(items), "status": status, "seconds": round(time.time() - t0, 1)}
        print(f"[{key}] {len(items)}개 ({info['seconds']}s) {status}", file=sys.stderr, flush=True)
        return key, info, [p.to_dict() if hasattr(p, "to_dict") else p for p in items]

    # 사이트별 수집은 서로 독립적인 네트워크 작업이라 동시에 돌린다
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for key, info, items in ex.map(run_site, targets):
            # 몰이 일시적으로 느려 실패해도 그 몰 상품이 사라지지 않게 이전 결과를 쓴다
            if not items and prev_by_site.get(key):
                kept = prev_by_site[key]
                info = {**info, "count": len(kept), "status": f"{info['status']} (이전 데이터 유지)",
                        "stale_since": previous.get("sites", {}).get(key, {}).get("stale_since") or previous.get("collected_at", "")}
                items = kept
                print(f"[{key}] 수집 실패 → 이전 {len(kept)}개 유지", file=sys.stderr, flush=True)
            meta[key] = info
            products += items

    if args.site:
        products = [p for p in previous.get("products", []) if p["site"] not in targets] + products
        meta = {**previous.get("sites", {}), **meta}

    out = {"collected_at": datetime.now().isoformat(timespec="seconds"), "sites": meta, "groups": GROUPS, "products": products}
    _save(out)
    print(f"총 {len(products)}개 저장 -> {DATA_DIR / 'products.json'}", file=sys.stderr)


def _save(out: dict):
    # 원본은 재분류용. 용량이 커서 저장소에는 gzip 형태(snapshot)만 올리고,
    # 다음 수집이 이것을 되살려 실패한 몰의 이전 데이터를 유지한다.
    raw = json.dumps(out, ensure_ascii=False)
    (DATA_DIR / "products.json").write_text(raw, encoding="utf-8")
    with gzip.open(DATA_DIR / "snapshot.json.gz", "wb", compresslevel=6) as f:
        f.write(raw.encode("utf-8"))
    merged = build(out["collected_at"], out["sites"], out["groups"], out["products"])
    # file:// 로 열어도 fetch 없이 읽을 수 있도록 스크립트 형태로 저장
    (DATA_DIR / "products.js").write_text("window.__PRODUCTS__=" + json.dumps(merged, ensure_ascii=False, separators=(",", ":")) + ";", encoding="utf-8")
    _stamp_version(out["collected_at"])
    print(f"묶음 {len(merged['p'])}종 / 판매처 {sum(len(e['o']) for e in merged['p'])}건", file=sys.stderr)


def _stamp_version(collected_at: str):
    """브라우저가 예전 데이터를 캐시해 보여주지 않도록 script 태그에 수집 시각을 박는다."""
    page = DATA_DIR.parent / "index.html"
    v = re.sub(r"\D", "", collected_at)
    page.write_text(re.sub(r'(<script src="data/products\.js)(\?v=\d+)?(">)', rf"\1?v={v}\3",
                           page.read_text(encoding="utf-8")), encoding="utf-8")


def _load_doc() -> dict:
    f = DATA_DIR / "products.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


if __name__ == "__main__":
    main()
