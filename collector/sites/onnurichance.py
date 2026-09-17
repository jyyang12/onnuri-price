from .wisa import _collect

SITE = "onnurichance"
SITE_NAME = "온누리 찬스"


def collect():
    return _collect(SITE, SITE_NAME, "https://onnurichance.com")
