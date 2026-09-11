import json
from pathlib import Path
from itertools import combinations
from logic.schemas import Stock

def load_stocks(path=None):
    path = path or Path(__file__).resolve().parents[1] / 'data/stocks.json'
    stocks = [Stock.model_validate(s).model_dump() for s in json.loads(Path(path).read_text(encoding='utf-8'))]
    if len(stocks) != 20 or len({s['ticker'] for s in stocks}) != 20:
        raise ValueError('서로 다른 20개 주식 데이터가 필요합니다.')
    return stocks

def effective_risk(s):
    return 0.5*s['risk_score'] + 0.3*s['volatility'] + 0.2*s['max_drawdown']

def risk_limit(p):
    return min(9.0, max(3.5, 3.5 + .5*p.risk_tolerance - .15*p.loss_sensitivity))

def match_score(p,s):
    values = [.35*(10-abs(p.risk_tolerance-effective_risk(s))), .30*(10-abs(p.growth_preference-s['growth_score'])), .20*(10-abs(p.loss_sensitivity-s['stability_score'])), .10*(10-abs(p.time_horizon-(s['growth_score']*.6+s['stability_score']*.4))), .05*s['analyst_confidence']]
    return round(min(100,max(0,sum(values)*10)),1)

def selection_allowed(p, selected):
    # Demo policy, not a scientifically calibrated investment constraint.
    return all(effective_risk(s) <= risk_limit(p) for s in selected) and sum(effective_risk(s)>=7 for s in selected)<=1 and len({s['sector'] for s in selected})>=2

def select_stocks(p,stocks,exclude=()):
    candidates = [group for group in combinations(stocks,3) if selection_allowed(p,group) and tuple(sorted(s["ticker"] for s in group)) not in exclude]
    if not candidates:
        raise ValueError('위험도 제한을 만족하는 종목 조합이 없습니다.')
    return list(max(candidates,key=lambda group: sum(match_score(p,s) for s in group)+2*len({s['sector'] for s in group})+max(effective_risk(s) for s in group)-min(effective_risk(s) for s in group)))

def validate_selection(portfolio,p,stocks):
    catalog = {s['ticker']:s for s in stocks}
    if any(r.ticker not in catalog for r in portfolio.recommendations):
        raise ValueError('존재하지 않는 ticker입니다.')
    if not selection_allowed(p,[catalog[r.ticker] for r in portfolio.recommendations]):
        raise ValueError('서버 위험도 및 분산 제한 위반입니다.')
    return portfolio
