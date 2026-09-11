import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from ai.openai_client import api_enabled, DEMO_NOTICE
from ai.investor_analysis import analyze_investor
from ai.portfolio_recommendation import recommend_portfolio
from logic.questionnaire import QUESTIONS, TYPE_NAMES, SCORE_NAMES, validate_answers
from logic.schemas import InvestorProfile
from logic.stock_matcher import load_stocks

ROOT = Path(__file__).resolve().parent

def create_app(test_config=None):
    app = Flask(__name__, instance_path=str(ROOT/'instance'))
    app.config.update(SECRET_KEY=os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32),
        DATABASE=str(ROOT/'instance/jobs.sqlite3'), MAX_CONTENT_LENGTH=16384,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    if test_config:
        app.config.update(test_config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True,exist_ok=True)
    def connect():
        db = sqlite3.connect(app.config['DATABASE'],timeout=10)
        db.row_factory = sqlite3.Row
        return db
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, created REAL, status TEXT, answers TEXT, profile TEXT, portfolio TEXT, profile_source TEXT, portfolio_source TEXT)')
    stocks = load_stocks()

    @app.context_processor
    def context():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return dict(demo=not api_enabled(), demo_notice=DEMO_NOTICE, csrf=session['csrf'])

    @app.after_request
    def headers(response):
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        return response

    @app.before_request
    def csrf_check():
        if request.method == 'POST' and (not session.get('csrf') or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),session['csrf'])):
            return jsonify(error='페이지를 새로고침한 뒤 다시 시도해주세요.'),403

    def get_job():
        with connect() as db:
            return db.execute('SELECT * FROM jobs WHERE id=? AND created>?',(session.get('job',''),time.time()-3600)).fetchone()

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/questionnaire')
    def questionnaire():
        return render_template('questionnaire.html',questions=QUESTIONS)

    @app.post('/api/start')
    def start():
        data=request.get_json(silent=True)
        try:
            answers=validate_answers(data.get('answers') if isinstance(data,dict) else None)
        except ValueError as exc:
            return jsonify(error=str(exc)),400
        old=get_job()
        if old and old['status'] != 'done' and old['status'] != 'error':
            return jsonify(url=url_for('analyzing'))
        job=secrets.token_urlsafe(24)
        with connect() as db:
            db.execute('DELETE FROM jobs WHERE created<?',(time.time()-3600,))
            db.execute('INSERT INTO jobs (id,created,status,answers) VALUES (?,?,?,?)',(job,time.time(),'pending',json.dumps(answers)))
        session['job']=job
        return jsonify(url=url_for('analyzing'))

    @app.get('/analyzing')
    def analyzing():
        job=get_job()
        if not job: return redirect(url_for('questionnaire'))
        if job['status']=='done': return redirect(url_for('result'))
        return render_template('analyzing.html')

    @app.post('/api/<stage>')
    def run_stage(stage):
        if stage not in ('profile','portfolio'): return jsonify(error='잘못된 단계입니다.'),404
        job=get_job()
        if not job: return jsonify(error='분석이 만료되었습니다. 테스트를 다시 시작해주세요.'),404
        target='pending' if stage=='profile' else 'profile_done'
        if job[stage]: return jsonify(status='complete')
        with connect() as db:
            claimed=db.execute('UPDATE jobs SET status=? WHERE id=? AND status=?',(stage+'_running',job['id'],target)).rowcount
        if not claimed:
            return jsonify(error='분석 중이거나 이전 단계가 완료되지 않았습니다.',status=job['status']),409
        try:
            if stage=='profile':
                output,source=analyze_investor(json.loads(job['answers']))
                state='profile_done'
            else:
                output,source=recommend_portfolio(InvestorProfile.model_validate_json(job['profile']),stocks)
                state='done'
            with connect() as db:
                # stage comes exclusively from the fixed allowlist above.
                db.execute(f'UPDATE jobs SET {stage}=?, {stage}_source=?, status=? WHERE id=?',(output.model_dump_json(),source,state,job['id']))
            return jsonify(status='complete',source=source)
        except Exception:
            app.logger.error('Analysis stage failed: %s',stage)
            with connect() as db: db.execute("UPDATE jobs SET status='error' WHERE id=?",(job['id'],))
            return jsonify(error='분석을 완료하지 못했습니다. 테스트를 다시 시작해주세요.'),500

    @app.get('/result')
    def result():
        job=get_job()
        if not job or job['status']!='done': return redirect(url_for('questionnaire'))
        p=json.loads(job['profile']); stored=json.loads(job['portfolio'])
        if 'portfolios' not in stored:
            return redirect(url_for('questionnaire'))
        options=stored['portfolios']
        selected=request.args.get('plan',0,type=int)
        if selected not in (0,1,2): selected=0
        portfolio=options[selected]
        catalog={s['ticker']:s for s in stocks}
        cards=[dict(**r,stock=catalog[r['ticker']]) for r in portfolio['recommendations']]
        return render_template('result.html',profile=p,portfolio=portfolio,cards=cards,
            type_name=TYPE_NAMES[p['investor_type']],score_names=SCORE_NAMES, options=options, selected=selected,
            profile_source=job['profile_source'],portfolio_source=job['portfolio_source'])
    return app

if __name__ == '__main__':
    create_app().run(host='127.0.0.1',port=5000,debug=False)
