# 온누리 가격비교

온누리상품권으로 결제할 수 있는 온라인 쇼핑몰 16곳의 상품을 모아, 같은 상품을 몰별로 묶어 가격·할인·적립을 비교하는 도구입니다.

온누리상품권 사용처는 대부분 "온누리 전용 기획전" 안의 상품만 결제가 되기 때문에, 각 몰을 일일이 열어 검색하지 않으면 비교가 어렵습니다. 이 도구는 그 기획전 상품을 하루 한 번 모아 한 화면에서 검색하게 해 줍니다.

## 수집 대상

11번가 온누리마켓 · 현대홈쇼핑 온누리샵 · 공영쇼핑 디지털온누리샵 · 롯데ON 온누리상생스토어 · 지니어스몰 ·
온누리시장 · 온누리공공몰 · 온누리마켓 · 온누리굿데이 · 인더마켓온누리몰 · 온누리 찬스 · 꾹AI온누리몰 ·
온누리핫딜 · 우체국쇼핑 전통시장 · 온누리5일장 · 온누리팔도시장

대상 목록의 출처는 온누리상품권 공식 사이트의 [온라인 사용처](https://www.onnuri.gift/visit/market)입니다.

## 다른 PC에서 이어서 하기

수집 데이터는 저장소에 올리지 않으므로, 받아온 직후에는 화면에 띄울 데이터가 없습니다.
전체 수집(약 25분)을 다시 돌리는 대신 마지막 배포본을 내려받으면 바로 시작할 수 있습니다.

```bash
git clone https://github.com/jyyang12/onnuri-price
cd onnuri-price
pip install -r requirements.txt

python -m collector._fetch_data     # 마지막 수집분 내려받기 (약 50MB)
python -m http.server 8765          # http://127.0.0.1:8765
```

`preview.html` 을 열면 휴대폰 화면 크기로 미리 볼 수 있고, 화면 파일을 고치면 알아서 다시 불러옵니다.

## 실행

```bash
pip install -r requirements.txt

python -m collector.run                 # 16곳 전체 수집 (약 25분)
python -m collector.run --site 11st     # 특정 사이트만 갱신
python -m collector.run --reclassify    # 재수집 없이 분류·묶음만 다시 계산

python -m http.server 8765              # http://127.0.0.1:8765 에서 확인
```

수집 결과는 두 파일로 저장됩니다.

- `data/products.json` — 수집 원본. 재분류·디버깅용이며 저장소에는 올리지 않습니다.
- `data/products.js` — 같은 상품을 묶고 주소를 압축한 화면용 데이터. 이것만 배포됩니다.

## 구조

```
collector/
  run.py         실행기 (사이트별 병렬 수집 → 분류 → 묶음 → 저장)
  common.py      공통 스키마·세션·유틸
  taxonomy.py    통합 카테고리 분류 규칙
  brand.py       상품명에서 브랜드 추출 규칙
  merge.py       같은 상품 묶기 + 용량 압축
  sites/         사이트별 어댑터 (솔루션이 같은 몰은 wisa·youngcart 공용 모듈 사용)
index.html       검색·비교 화면 (서버 없이 data/products.js 만 읽음)
```

사이트를 추가하려면 `collector/sites/` 에 `SITE`, `SITE_NAME`, `collect()` 를 가진 모듈을 만들고 `sites/__init__.py` 의 `SITES` 에 등록하면 됩니다.

## 자동 갱신

GitHub Actions가 매주 월·목 04:00(KST)에 수집한 뒤, 화면 파일과 데이터만 담아 `deploy` 브랜치로 발행합니다.
주기는 `.github/workflows/collect.yml` 의 `cron` 한 줄이고, 저장소 Actions 탭에서 수동 실행도 됩니다.
호스팅은 그 브랜치를 바라봅니다. 수집 결과가 비정상이면(상품 1만 종 미만 또는 정상 사이트 8곳 미만) 발행을 건너뜁니다.

## 참고

- 개인이 가격을 비교해 보려고 만든 도구입니다. 각 몰이 공개한 목록 페이지만 정중한 간격으로 읽습니다.
- 가격·재고는 수집 시점 기준이라 실제와 다를 수 있습니다. 결제 전에 반드시 해당 몰에서 확인하세요.
- 상품이 여러 몰에 있을 때 같은 상품인지는 상품명으로 판단하므로, 용량·구성이 다른 상품이 함께 묶일 수 있습니다.
