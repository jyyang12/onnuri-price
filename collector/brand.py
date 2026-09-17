"""상품명 말머리 `[...]`에서 브랜드를 뽑는다. 판촉 문구가 섞여 있어 걸러낸다."""
import re

PREFIX = re.compile(r"^\s*[\[(]([^\])]{1,20})[\])]")

# 브랜드가 아니라 판촉·배송·규격 표시인 말머리
NOT_BRAND = re.compile(
    r"농할|온누리|추석|설날|명절|선물|세트|특가|할인|쿠폰|무료|배송|직송|당일|출발|도착"
    r"|품질보장|정품|국내산|수입산|원산지|신상|인기|베스트|BEST|한정|마감|단독|이벤트"
    r"|기획|균일가|랜덤|색상|사은품|증정|리뷰|적립|카드|페이백|타임|딜\b|오특|쟁여|대전"
    r"|제철|햇\b|냉장|냉동|신선|특선|택1|골라|모음|묶음|총\s*\d|\d+\s*개입?|\+\d"
    r"|쇼페|생방송|방송|라이브|주문폭주|재입고|앵콜|마지막|오늘만|단하루|최저가|반값"
    r"|무료체험|체험단|공동구매|공구|예약|사전|당첨|응모|추첨|덤|증량|용량|중량"
    r"|년\s*산|년산|\d{2,4}년|[0-9]+%|[0-9]+원",
    re.I,
)
SYMBOL_START = re.compile(r"^[\d★☆♥♡◆■●▶▷※!@#$%^&*+~\-_/\\]")


def extract(name: str) -> str:
    m = PREFIX.match(name or "")
    if not m:
        return ""
    tag = m.group(1).strip()
    if len(tag) < 2 or SYMBOL_START.search(tag) or NOT_BRAND.search(tag):
        return ""
    # 괄호가 닫히지 않은 경우(예: "26년추석[해울림") 등 깨진 값 제외
    if any(c in tag for c in "[]()"):
        return ""
    return tag
