# GitHub에 올리고 사이트 주소 받기

Python 파일을 유지하면서 GitHub Pages로 데모 사이트를 공개할 수 있도록 `index.html`을 추가했습니다. Flask용 `app.py`, `ai/`, `logic/`, `templates/`는 그대로 있습니다.

## 가장 간단한 업로드 방법

1. ZIP을 풀고 `project` 폴더를 엽니다.
2. GitHub에서 새 저장소를 만듭니다. 무료 계정이라면 Public 저장소를 사용합니다.
3. **Add file → Upload files**에서 `project` **안의 파일과 폴더**를 올립니다. `index.html`이 저장소 최상위에 있어야 합니다. ZIP 자체나 바깥 `project` 폴더를 통째로 올리지 마세요.
4. **Settings → Pages → Build and deployment → Source**에서 **Deploy from a branch**를 선택합니다.
5. **main**, **/ (root)**를 고르고 **Save**를 누릅니다.
6. 배포 후 같은 화면의 **Visit site**를 누릅니다. 보통 주소는 `https://깃허브아이디.github.io/저장소이름/` 형태입니다.

이 방식은 `index.html`과 `static/`만 있어도 됩니다. 숨김 파일이 브라우저 업로드에서 빠져도 정적 데모는 실행됩니다. 전체 Python 코드도 유지하려면 함께 업로드하세요. 실제 `.env`, `instance/`, `.venv/`, `__pycache__/`는 올리지 마세요. 제공 ZIP에는 이 파일들이 없습니다. **웹에서 직접 업로드할 때는 `.gitignore`가 파일 선택을 막아주지 않습니다.**

## Git으로 업로드할 때: 포함된 자동 배포 사용

`.github/workflows/pages.yml`을 포함해 전체 프로젝트를 저장소 루트에 커밋한 경우, Pages의 **Source를 GitHub Actions**로 설정하세요. 저장소 **Actions → Deploy demo to GitHub Pages → Run workflow**로 첫 배포를 실행할 수 있습니다. 이후 `main`에 push하면 자동 배포됩니다. 기본 브랜치가 다르면 workflow의 `branches`를 해당 이름으로 바꾸세요.

이 워크플로는 공개 화면에 필요한 `index.html`, CSS, 데모 JS만 배포합니다. Python 소스는 저장소에 유지되며 웹 배포 산출물에는 포함하지 않습니다. 공개 저장소의 소스 자체는 공개됩니다.

## API와 Python은 어떻게 되나요?

| 실행 방식 | 데모 분석 | 실제 OpenAI | Python 실행 |
|---|---|---|---|
| GitHub Pages의 index.html | 가능 | 불가 | 불가 |
| 기존 python app.py | 가능 | 서버 .env 설정 시 가능 | 가능 |

GitHub Pages는 정적 호스팅이므로 Python 서버를 실행하지 않습니다. Pages에 API 키를 넣어도 기존 Flask API가 실행되는 것은 아닙니다. 공개 HTML/JS에 키를 넣지 마세요. 실제 AI 기능까지 온라인으로 제공하려면 기존 Flask 앱을 Python 서버 호스팅에 배포해야 합니다.

## 정적 버전 특징

- 서버·설치·API 키 없이 설문부터 결과까지 브라우저에서 실행합니다.
- `#test`, `#analyzing`, `#result`를 사용하여 저장소 하위 URL에서 새로고침해도 404가 발생하지 않습니다.
- 답변과 결과는 현재 페이지 메모리에만 보관하며 새로고침하면 초기화됩니다.
- 브라우저에서 네트워크 API 호출 없이 규칙 기반 성향 분석, 20개 종목 비교, 3종목 분산 및 15~50%·합계 100% 제한을 적용합니다.
- CSS는 Flask와 공유하고 JavaScript는 `pages*.js`로 분리했습니다. Flask의 `main.js`는 유지했습니다.
- `index.html`을 로컬에서 더블클릭해도 실행할 수 있도록 데이터를 JS 파일에 포함했습니다. **index.html만 복사하지 말고 static 폴더도 함께 유지하세요.**

## 나중에 설문이나 데이터를 수정한다면

원본 `logic/questionnaire.py`, `data/stocks.json`, 시작/설문 템플릿을 수정한 뒤 다음 명령으로 정적 HTML과 데이터 JS를 갱신하세요.

```bash
python scripts/build_static.py
```

기존 `requirements.txt`의 Jinja2(Flask 의존성)를 사용합니다. 생성된 파일도 커밋해야 합니다. 계산 규칙을 바꿀 때는 Python 로직과 `static/js/pages-logic.js` 양쪽을 수정해야 합니다.

공식 안내: [사이트 만들기](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site), [GitHub Actions 배포](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
