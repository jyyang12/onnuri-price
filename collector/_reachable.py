"""개발용: 실행 환경에서 각 몰에 접속되는지 확인한다.

해외 IP를 막는 몰이 있어 CI에서 수집 가능한 범위를 미리 파악하는 데 쓴다.
    python -m collector._reachable
"""
import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from .common import session

PROBES = {
    "11st": "https://plan.11st.co.kr/plan/front/exhibitions/2210481/detail",
    "hmall": "https://www.hmall.com/md/dpa/searchSpexSectItem?sectId=3132118",
    "gongyoung": "https://www.gongyoungshop.kr/exhibition/ebtDetail.do?ebtNo=4328",
    "lotteon": "https://pbf.lotteon.com/display/v2/dpShop/seltMainShop?dshopNo=57821&mdiaCd=PC",
    "genius": "https://luxurysystem.co.kr/",
    "onnurimall": "https://www.onnuri-mall.co.kr/",
    "ongong": "https://www.ongong.kr/shop/",
    "nurimarket": "https://nurimarket.co.kr/",
    "onnurigood": "https://www.onnurigood.com/",
    "inthemarket": "https://inthemarket.co.kr/",
    "onnurichance": "https://onnurichance.com/",
    "onnuriai": "https://onnuri.ai/",
    "onnurideal": "https://onnurideal.com/",
    "epost": "https://mall.epost.go.kr/fo/pavln/sijangAll.do",
    "onnuri5": "https://www.onnuri5.com/",
    "ejangter": "https://e-jangter.com/Extmall/Onnuri.aspx",
}


def check(item):
    key, url = item
    s = session()
    s.adapters.clear()  # 재시도 없이 한 번만 — 차단 여부만 보면 된다
    t0 = time.time()
    try:
        r = s.get(url, timeout=25, stream=True)
        return key, f"{r.status_code} {len(r.content) // 1024}KB", time.time() - t0
    except Exception as e:
        return key, f"{type(e).__name__}", time.time() - t0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(check, PROBES.items()))
    bad = []
    for key, res, secs in rows:
        ok = res[:1] == "2"
        print(f"{'OK  ' if ok else 'FAIL'} {key:14} {res:14} {secs:5.1f}s")
        if not ok:
            bad.append(key)
    print(f"\n접속 가능 {len(rows) - len(bad)}/{len(rows)}" + (f" | 실패: {' '.join(bad)}" if bad else ""))


if __name__ == "__main__":
    main()
