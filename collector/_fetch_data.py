"""다른 PC에서 이어서 작업할 때 마지막 수집분을 내려받는다.

25분짜리 전체 수집을 다시 돌리지 않고 배포본을 그대로 쓴다.
    python -m collector._fetch_data
"""
import gzip
import io
import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/jyyang12/onnuri-price/deploy/data/"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get(name: str) -> bytes:
    with urllib.request.urlopen(BASE + name, timeout=120) as r:
        return r.read()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    DATA_DIR.mkdir(exist_ok=True)

    print("화면용 데이터 내려받는 중...")
    js = get("products.js")
    (DATA_DIR / "products.js").write_bytes(js)

    print("수집 원본 내려받는 중...")
    raw = gzip.decompress(get("snapshot.json.gz"))
    (DATA_DIR / "products.json").write_bytes(raw)
    (DATA_DIR / "snapshot.json.gz").write_bytes(gzip.compress(raw, 6))

    doc = json.loads(raw)
    print(f"\n{doc['collected_at']} 수집분 · 상품 {len(doc['products']):,}건 / 사이트 {len(doc['sites'])}곳")
    print(f"저장 위치: {DATA_DIR}")
    print("\n이제 `python -m http.server 8765` 로 화면을 열 수 있습니다.")


if __name__ == "__main__":
    main()
