import re
from dataclasses import dataclass, asdict
from typing import Optional

import requests

try:
    import truststore  # 사내망 TLS 검사 프록시의 인증서를 Windows 저장소에서 신뢰
    truststore.inject_into_ssl()
except ImportError:
    pass

UA ="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"


def session() -> requests.Session:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"})
    retry = Retry(total=4, connect=4, read=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=frozenset(["GET", "POST"]))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


@dataclass
class Product:
    site: str
    site_name: str
    product_id: str
    name: str
    price: Optional[int]
    orig_price: Optional[int]
    discount_rate: Optional[int]
    benefit: str
    free_delivery: Optional[bool]
    url: str
    image: str
    category: str
    rating: Optional[float]
    review_count: Optional[int]
    sales: Optional[int] = None      # 주문수/판매량 (사이트가 제공할 때만)
    featured: bool = False           # 사이트 메인/BEST 노출 상품
    group: str = ""                  # 통합 카테고리 (taxonomy.classify)

    def to_dict(self):
        return asdict(self)


def to_int(v) -> Optional[int]:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return int(v)
    digits = re.sub(r"[^\d]", "", str(v))
    return int(digits) if digits else None


def to_float(v) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


ICON_SRC = re.compile(
    r"/(?:public|common|skin|assets?|static)/(?:img|image)|/shop/img/|/data/category/"
    r"|/upfiles/(?:normal|icon)/|_tag\.|_ic\.|sticker|emblem|/icon|\.svg(?:\?|$)",
    re.I,
)


def pick_image(block: str) -> str:
    """상품 블록에서 실제 상품 이미지를 고른다. 배지·별점 같은 아이콘 경로는 건너뛴다."""
    for m in re.finditer(r'<img[^>]+src="([^"]+)"', block):
        if not ICON_SRC.search(m.group(1)):
            return m.group(1)
    return ""


def rate(price, orig) -> Optional[int]:
    if price and orig and orig > price:
        return round((orig - price) / orig * 100)
    return None
