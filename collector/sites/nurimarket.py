from .youngcart import _collect

SITE = "nurimarket"
SITE_NAME = "온누리마켓"


def collect():
    # 목록 페이지에 페이징이 없어 말단 카테고리(4자리 이상)를 전부 순회
    return _collect(SITE, SITE_NAME, "https://nurimarket.co.kr", lambda c: True, paged=False)
