from .wisa import _collect

SITE = "inthemarket"
SITE_NAME = "인더마켓온누리몰"


def collect():
    return _collect(SITE, SITE_NAME, "https://inthemarket.co.kr")
