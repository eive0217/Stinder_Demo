"""Export a key-free GitHub Pages entrypoint; existing Flask files are untouched."""
import ast
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
ROOT=Path(__file__).resolve().parents[1]
# Read constants without importing the backend or loading its .env.
tree=ast.parse((ROOT/'logic/questionnaire.py').read_text(encoding='utf-8'))
constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)}
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=select_autoescape())
env.globals['url_for']=lambda endpoint,filename: './static/'+filename
home=env.get_template('index.html').render(demo=False,csrf='').split('<main>')[1].split('</main>')[0].replace('href="/questionnaire"','href="#test"')
quiz=env.get_template('questionnaire.html').render(demo=False,csrf='',questions=constants['QUESTIONS']).split('<main>')[1].split('</main>')[0]
quiz=quiz.replace('AI 모드에서는 제출한 10개 질문과 답변이 OpenAI로 전송됩니다.','이 데모는 브라우저 안에서만 분석하며 답변을 외부로 전송하지 않습니다.')
analysis=env.get_template('analyzing.html').render(demo=False,csrf='').split('<main>')[1].split('</main>')[0].replace('href="/questionnaire"','href="#test"').replace('AI가 투자 성향을 분석하고 있습니다...','투자 성향을 분석하고 있습니다...').replace('분석에는 최대 약 2분이 걸릴 수 있습니다.','규칙 기반 데모 분석을 진행하고 있습니다.')
html='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 투자 성향 매칭</title><meta name="description" content="10가지 일상 속 선택으로 알아보는 투자 성향과 교육용 모델 포트폴리오"><link rel="stylesheet" href="./static/css/style.css"><script defer src="./static/js/pages-data.js"></script><script defer src="./static/js/pages-logic.js"></script><script defer src="./static/js/pages.js"></script></head><body><header><a class="brand" href="#home"><span class="brand-mark">↗</span> AI 투자 성향 매칭</a><span class="pill">교육용 프로토타입</span></header><main><div class="notice">규칙 기반 데모 모드 · 모든 종목 수치는 가상 데이터입니다.</div>'''
html+='<div id="view-home">'+home+'</div><div id="view-test" hidden>'+quiz+'</div><div id="view-analyzing" hidden>'+analysis+'</div><div id="view-result" hidden></div>'
html+='''<noscript>테스트를 이용하려면 브라우저의 JavaScript를 활성화해주세요.</noscript></main><footer>본 결과는 교육 및 실험 목적의 예시이며 실제 투자 조언이 아닙니다.<br>실제 투자 결정은 개인의 판단과 책임에 따라 이루어져야 합니다.</footer></body></html>'''
(ROOT/'index.html').write_text(html,encoding='utf-8')
data={'questions':constants['QUESTIONS'],'types':constants['TYPE_NAMES'],'scores':constants['SCORE_NAMES'],'stocks':json.loads((ROOT/'data/stocks.json').read_text(encoding='utf-8'))}
(ROOT/'static/js/pages-data.js').write_text('globalThis.DEMO_DATA = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
(ROOT/'.nojekyll').touch()
print('Generated index.html and public demo data (no environment or API keys read).')
