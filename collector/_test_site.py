"""개발용: python -m collector._test_site <site> — 한 사이트만 수집해 요약 출력."""
import io
import sys
import time
import traceback
from collections import Counter

from .sites import SITES

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
key = sys.argv[1]
t0 = time.time()
try:
    items = SITES[key].collect()
except Exception:
    traceback.print_exc()
    sys.exit(1)
print(f"[{key}] {len(items)}개 {time.time() - t0:.0f}s")
print("category:", Counter(p.category.split(" · ")[0] for p in items).most_common(8))
print("price None:", sum(1 for p in items if not p.price), "| orig:", sum(1 for p in items if p.orig_price),
      "| free:", sum(1 for p in items if p.free_delivery), "| img:", sum(1 for p in items if p.image), "| name empty:", sum(1 for p in items if not p.name))
for p in items[:2]:
    print(p.to_dict())
