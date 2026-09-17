from .wisa import _collect

SITE = "onnurigood"
SITE_NAME = "온누리굿데이"


def collect():
    return _collect(SITE, SITE_NAME, "https://www.onnurigood.com")
