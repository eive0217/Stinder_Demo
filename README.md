# 미국 ETF 성향 매칭

10개 행동형 설문 → 성향 분석 → 미국 상장 ETF 20개 비교 → 추천안 A/B/C를 제공합니다. 각 안은 서로 다른 ETF 3개, 비중 15~50%, 합계 100%입니다. 각 안은 대안이므로 투자금 전액을 선택한 한 안에 배분합니다.

## 데이터 범위

미국 상장 Vanguard ETF 20개를 시연용 목록으로 사용합니다. 운용사 선정 자체가 추천이나 우열 판단을 의미하지 않습니다.

VOO, VTI, VUG, VTV, VIG, VYM, VGSH, VGIT, BSV, BND, VTIP, VCSH, VO, VB, VGT, VHT, VNQ, VDE, VDC, VPU.

상품명과 투자 대상은 [운용사 상품 목록](https://investor.vanguard.com/investment-products/list/etfs)을 참고했습니다. **운용보수 포함 모든 숫자는 가상 예시**이며 실시간 수집 자료가 아닙니다. `data/etfs.json`의 `data_kind=synthetic`으로 구분합니다. 주식용 목표가, 예상 상승 여력, 애널리스트 의견은 제거했습니다.

미국 주식형과 채권형 상품을 포함합니다. 변동성·최대 낙폭·위험·성장·안정성·유동성은 0~10의 가상 점수이며 실제 수익률이나 낙폭 비율이 아닙니다. 운용보수 단위는 연 %입니다. 원화 입력 금액은 비중 계산용이며 환전·주문 수량 계산이 아닙니다.

## 설치 및 실행

Python 3.10 이상. project 폴더에서:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

http://127.0.0.1:5000 에 접속합니다. Windows에서는 `.venv\Scripts\activate`로 활성화하며 gunicorn은 Linux 배포용입니다.

키가 없으면 규칙 기반 데모로 동작합니다. 실제 API 사용 시 `.env`에 OPENAI_API_KEY를 설정합니다. OPENAI_MODEL 기본값은 gpt-4.1-mini입니다. `.env`를 저장소에 올리지 마세요.

## Render

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn 'app:create_app()' --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
- 환경변수: `OPENAI_API_KEY`, `FLASK_SECRET_KEY`(고정 무작위 값), `OPENAI_MODEL`(선택)

GitHub에 커밋 후 Render에서 재배포합니다. 환경변수는 기존과 동일합니다. 이전 주식 결과는 재사용하지 않으므로 새 테스트를 진행하세요. 파일 교체 시 구버전 `data/stocks.json`, `logic/stock_matcher.py`는 삭제하세요.

## 구조

- `app.py`: Flask 라우팅, 세션, 단계별 SQLite 저장, 추천안 선택
- `logic/questionnaire.py`: 설문과 성향 fallback
- `logic/schemas.py`: ETF, 성향, 포트폴리오 3세트 검증
- `logic/etf_matcher.py`: ETF 목록 로드, 매칭과 위험·중복 제한
- `logic/allocation.py`: 정수 비중 배분
- `ai/openai_client.py`: 환경변수, OpenAI SDK 공통 처리
- `ai/investor_analysis.py`: 1차 성향 분석
- `ai/portfolio_recommendation.py`: 2차 ETF 추천안 3개 생성 및 fallback
- `data/etfs.json`: 가상 ETF 데이터
- `templates/`, `static/`: 흑백 UI
- `index.html`, `static/js/pages*.js`: GitHub Pages용 브라우저 데모
- `scripts/build_static.py`: 템플릿·설문·데이터에서 정적 파일 생성

## API와 검증

정상 AI 모드는 총 2회 호출합니다. 1차는 모든 설문 질문과 답변, 2차는 성향과 전체 ETF 데이터를 전달합니다. 2차 응답은 `{"portfolios": [{"portfolio_summary": "...", "recommendations": [...]}, ...]}` 형태입니다. portfolios 길이는 3이고 각 recommendations 길이도 3입니다.

OpenAI Responses API의 `responses.parse`와 Pydantic Structured Outputs를 사용합니다. SDK 자동 재시도는 0회, 타임아웃은 45초입니다. API 오류·응답 거부·불완전 JSON·서버 검증 실패 시 해당 단계를 fallback으로 대체하며 화면에서 표시합니다. 실제 유료 API 요청은 테스트하지 않았습니다.

비중 합계·상하한·중복·허용 ticker·매칭 점수·필수 필드 등을 서버에서 검증합니다. 같은 세 ETF 조합을 다른 추천안으로 반복하지 않습니다. 세 안에 동일한 성향 위험 제한을 적용합니다.

유효 위험도 = risk_score×0.5 + volatility×0.3 + max_drawdown×0.2. 종목별 상한 = min(9, max(3.5, 3.5 + 위험 감수×0.5 - 손실 민감도×0.15)). 유효 위험 7 이상은 안별 최대 1개, 최소 2개 ETF 유형을 포함하고 동일 overlap_group은 중복 금지입니다. VOO/VTI와 VIG/VYM은 각각 같은 중복 그룹입니다. 이는 보유자산을 직접 비교한 정량 중복 분석이 아닌 시연용 규칙이며 다른 그룹 간에도 실제 보유자산이 겹칠 수 있습니다.

fallback 매칭: 위험 일치 35%, 성장 일치 30%, 손실 민감도/안정성 20%, 장기 성향 10%, 유동성 3%, 비용 2%. 비용 점수는 max(0, 10-10×운용보수)입니다. 제한을 만족하는 서로 다른 상위 세 조합을 선택하며 비중은 위험 조정 점수로 배분합니다. 합법적인 조합이 없으면 제한을 풀지 않고 오류 처리합니다.

## 상태 보존

SQLite는 `instance/jobs.sqlite3`에 생성됩니다. 결과 접근은 1시간이며 만료 기록은 다음 테스트 생성 시 삭제합니다. Render 임시 저장소는 재시작·절전·재배포 시 기록이 사라질 수 있습니다. 서버 종료로 진행 중 작업이 남은 경우 새 세션 또는 만료 후 다시 시도합니다. 공개 서비스 운영에는 별도 영구 DB, 요청 제한, 중단 작업 복구가 필요합니다.

## GitHub Pages와 테스트

Pages는 Python/API 실행 없이 데모만 제공합니다. 자세한 배포 안내는 GITHUB_PAGES.md를 참고하세요. 정적 파일 갱신: `python scripts/build_static.py`. 계산식 변경 시 Python과 pages-logic.js 양쪽을 수정합니다.

```bash
python -m unittest discover -s tests -v
node tests/test_pages.cjs
```

본 결과는 교육 및 실험 목적의 예시이며 실제 투자 조언이 아닙니다.
