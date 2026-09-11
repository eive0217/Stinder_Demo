# AI 투자 성향 매칭

**GitHub Pages용 `index.html` 추가 완료:** Python 파일을 그대로 유지하며 사이트를 공개하는 방법은 [GITHUB_PAGES.md](GITHUB_PAGES.md)를 확인하세요. Pages는 데모 모드, Flask는 실제 OpenAI 연동을 지원합니다.

한국어 Flask 웹 프로토타입입니다. 10개의 행동형 질문 → 투자 성향 분석 → 20개 가상 종목 비교 → 3종목 포트폴리오 순서로 작동합니다. 모든 금융 수치와 애널리스트 의견은 교육용 더미 데이터이며 실제 투자 조언이 아닙니다.

## 설치 및 실행

Python 3.10 이상이 필요합니다. 터미널에서 이 README가 있는 `project` 폴더로 이동한 뒤 실행합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Windows에서는 가상환경 활성화 명령으로 `.venv\Scripts\activate`를 사용합니다. 브라우저에서 http://127.0.0.1:5000 을 여세요.

`.env`의 `OPENAI_API_KEY`가 비어 있으면 바로 데모로 실행됩니다. 화면에 다음 문구가 표시됩니다.

> OpenAI API 키가 설정되지 않아 데모 분석 모드로 실행합니다.

실제 API를 사용하려면 `.env`를 로컬 편집기로 열어 키를 설정한 뒤 서버를 재시작하세요. 키를 프론트엔드나 저장소에 넣지 마세요.

```dotenv
OPENAI_API_KEY=여기에_본인_API_키
OPENAI_MODEL=gpt-4.1-mini
FLASK_SECRET_KEY=충분히_긴_무작위_문자열
```

`OPENAI_MODEL`은 Structured Outputs를 지원하며 본인 API 프로젝트에서 접근할 수 있는 모델로 변경할 수 있습니다. 키가 있어도 인증·한도·타임아웃·모델 접근 오류가 발생하면 해당 단계만 규칙 기반 결과로 대체합니다. 키는 서버에서만 읽으며 브라우저에 전송하지 않습니다. `.env`, SQLite DB, 가상환경은 `.gitignore`에 포함했습니다.

## 프로젝트 구조

```text
project/
  app.py                         Flask 라우팅, 세션, 단계별 서버 저장
  ai/
    openai_client.py              .env 로드, SDK 및 Structured Outputs 공통 호출
    investor_analysis.py         1차 호출, 설문 해석 프롬프트
    portfolio_recommendation.py  2차 호출, 추천 프롬프트 및 fallback
  logic/
    questionnaire.py             10문항, 입력 검증, 성향 점수·타입 fallback
    schemas.py                   Pydantic JSON 및 종목 데이터 검증
    stock_matcher.py              데이터 로드, 매칭, 위험도·분산 제한
    allocation.py                 정수 비중 배정
  data/stocks.json                20개 가상 주식 데이터
  templates/
    base.html
    index.html
    questionnaire.html
    analyzing.html
    result.html
  static/css/style.css
  static/js/main.js
  tests/test_app.py
  .env.example
  .gitignore
  requirements.txt
  README.md
```

## API 설계

공식 [Structured Outputs 문서](https://developers.openai.com/api/docs/guides/structured-outputs)를 기준으로 OpenAI Python SDK의 `client.responses.parse(text_format=Pydantic모델)`을 사용합니다. JSON mode만 사용하는 구현이 아닙니다.

1. `POST /api/start`: 길이 10, 값 0·1·2인 정수 배열만 받습니다. 클라이언트가 점수나 종목을 정할 수 없습니다.
2. `POST /api/profile`: 질문·모든 선택지·실제 선택 답변을 전달합니다. 네 점수와 지정 타입, 한국어 요약을 받습니다. 실제 소득·자산·나이 등을 추측하지 않도록 지시합니다.
3. `POST /api/portfolio`: 서버에 저장된 성향과 20개 전체 종목 데이터를 전달합니다. 종목 3개, 비중, 매칭 점수, 이유와 포트폴리오 설명을 받습니다.
4. 결과 페이지는 검증된 서버 저장 결과만 렌더링합니다. 입력 금액은 브라우저 안에서만 사용합니다.

정상 AI 모드는 **정확히 2번**, 데모 모드는 **0번** 호출합니다. 실패 시 추가 재시도 대신 안전한 fallback을 사용하도록 선택했습니다. SDK의 자동 재시도도 `max_retries=0`으로 껐습니다. 각 단계에 SQLite 원자적 상태 전환을 적용하여 새로고침·중복 단계 요청에서 이미 완료되거나 진행 중인 API를 다시 호출하지 않습니다. 사용자가 완료 후 새 테스트를 하면 새로운 2단계 실행입니다.

`store=False`, 단계별 45초 타임아웃을 사용합니다. 거부·불완전한 응답·SDK 오류·검증 실패를 fallback으로 처리합니다. `store=False`는 OpenAI의 모든 데이터 보존이 없음을 의미하지 않으며 계정의 데이터 정책이 별도 적용됩니다.

## Python 검증 및 위험 제한

- 네 성향 점수 0~10, 네 타입 중 하나, 필수 필드와 문자열 길이를 검증합니다.
- 추천 길이 3, 중복 ticker 금지, 허용 목록 ticker, 정수 비중 15~50, 합계 100, 매칭 점수 0~100을 검증합니다.
- 추가 필드, boolean을 숫자로 쓰는 입력, NaN/Infinity를 거부합니다.
- 종목 수 20, 종목 중복, 지표 범위, 최저 ≤ 평균 ≤ 최고 목표가를 검증합니다.
- 유효 위험도 = 위험 점수×0.5 + 변동성×0.3 + 최대 낙폭 위험×0.2.
- 허용 위험도 = `min(9, max(3.5, 3.5 + 0.5×위험 감수 - 0.15×손실 민감도))`.
- 모든 추천 종목이 허용 위험도 이하여야 합니다. 유효 위험도 7 이상은 최대 1개, 최소 2개 업종을 포함합니다.
- 위 조건을 위반한 AI 결과는 그대로 보여주거나 몰래 수정하지 않고 전체 추천 단계를 fallback으로 대체합니다. 실제 AI/fallback 사용 여부를 결과 화면에 단계별로 표시합니다.

이 임계값은 시연용 정책이며 검증된 재무 모형이 아닙니다. 더미 데이터를 교체할 때도 안전한 3종목 조합을 구성할 수 있어야 하며, 조합이 없으면 위험 제한을 완화하지 않고 오류로 종료합니다.

## 규칙 기반 fallback

설문은 선택지 0·1·2에 문항별 네 요소 가중치를 적용해 각각 0~10으로 정규화합니다. 손실 민감도는 선택지 방향을 반대로 계산합니다. 위험과 성장, 손실 민감도로 네 타입을 결정합니다.

매칭 점수는 위험 일치도 35%, 성장 일치도 30%, 손실 민감도/안정성 일치도 20%, 장기 성향 10%, 애널리스트 신뢰도 5%입니다. 단순 상위 3개 대신 가능한 3종목 조합을 평가해 위험 제한과 업종 분산을 만족하는 조합을 선택합니다. 비중은 매칭 점수와 사용자 위험·손실 성향, 종목 유효 위험도를 반영하여 15%부터 남은 정수 퍼센트를 최대 50%까지 배분합니다.

`expected_upside`는 퍼센트, 목표가는 가상 USD입니다. `volatility`와 `max_drawdown`은 실제 변동률·낙폭 %가 아니라 **0~10의 가상 위험 점수**입니다. 매칭 점수는 수익 확률이 아닙니다. 투자 금액 예시는 원 단위 내림 후 나머지를 소수부가 큰 항목부터 배분해 입력 총액과 합계가 일치합니다.

## 상태 저장 및 운영 범위

SQLite는 처음 실행할 때 `instance/jobs.sqlite3`에 생성됩니다. 브라우저에는 서명된 세션 식별자와 CSRF 토큰만 보관하고 답변·결과는 서버 DB에 저장합니다. 분석은 1시간 동안 접근 가능하며 만료 행은 다음 테스트 생성 시 삭제됩니다. 이는 자동 정시 삭제 작업이 아닙니다. 데모 종료 후 DB를 지워 기록을 삭제할 수 있습니다.

개발 서버는 로컬 127.0.0.1에만 바인딩하며 디버그 모드는 꺼져 있습니다. 서버가 API 호출 도중 종료되면 진행 상태는 만료까지 남습니다. 서버 재시작 시 기본 임시 세션 키가 바뀌므로 새 테스트를 시작할 수 있습니다. 고정 `FLASK_SECRET_KEY` 사용 중에는 세션 쿠키를 지우거나 1시간 후 다시 시작하세요. 실제 공개 배포에는 인증·요청 제한·HTTPS·작업 큐와 중단 작업 복구·보존 정책 등이 추가로 필요합니다.

요청된 Python/Flask 서버 구조를 유지한 로컬 실행 프로젝트이며 Cloudflare Workers용으로 변환하거나 외부에 배포하지 않았습니다.

## 테스트

```bash
python -m unittest discover -s tests -v
```

API 키 없이 실행합니다. Flask 전체 흐름, 입력·CSRF 검증, 잘못된 JSON과 ticker, 위험 제한, 랜덤 답변 조합의 fallback, API 모의 응답, 거부·불완전 응답, 정상 요청 2회 및 중복 요청 방지를 검증합니다. 실제 유료 OpenAI 호출은 본인 키를 설정한 후 별도 확인해야 합니다.

## 향후 확장

StockAnalysis.com 등의 실제 데이터 연결은 향후 작업입니다. 데이터 수집 모듈에서 현재 종목 스키마로 변환하고 출처·기준일·단위를 추가하면 매칭/AI/UI를 유지할 수 있습니다. OpenAI 연동은 이미 구현되어 있으며 데이터 크롤링은 포함하지 않습니다.
