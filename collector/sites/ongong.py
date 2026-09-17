from .youngcart import _collect

SITE = "ongong"
SITE_NAME = "온누리공공몰"


def collect():
    return _collect(SITE, SITE_NAME, "https://www.ongong.kr", lambda c: len(c) == 2, paged=True)
