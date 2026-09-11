from ai.openai_client import structured_call, api_enabled, RECOVERABLE, report_fallback
from logic.schemas import Portfolio, PortfolioOptions
from logic.stock_matcher import select_stocks, validate_selection, match_score, risk_limit
from logic.allocation import allocate
SYSTEM_PROMPT = """포트폴리오 추천안을 정확히 3개 생성하여 portfolios 배열로 반환하세요. 각 추천안은 서로 다른 종목 조합이어야 합니다. 안 사이에 일부 종목 중복은 허용하되 동일한 세 종목 조합은 금지합니다. 각 안의 요약에서 다른 안과의 차이를 설명하세요. 모든 안에 동일한 사용자 위험 제한을 적용하세요. 다음 조건은 각 추천안에 개별적으로 적용합니다. 교육용 가상 주식 데이터만 사용해 한국어 포트폴리오를 만드세요. USER PROFILE과 STOCK DATA의 20개 종목을 비교하고 정확히 서로 다른 3개를 추천하세요. 비중은 정수, 각각 15~50, 합계 100입니다. match_score는 0~100입니다. 위험 감수와 손실 민감도를 고려하고 expected_upside만 극대화하지 마세요. volatility와 max_drawdown을 반드시 평가하세요. 서버 정책: 종목별 effective_risk=0.5*risk_score+0.3*volatility+0.2*max_drawdown은 전달된 risk_limit 이하, effective_risk>=7 종목은 최대 1개, 최소 2개 sector를 포함하세요. 재정 상태를 추측하지 말고 수익을 보장하지 마세요. 가상 데이터임을 전제로 추천 이유와 분산·비중 설명을 작성하세요."""

def fallback_portfolio(p,stocks,exclude=()):
    selected = select_stocks(p,stocks,exclude)
    weights = allocate(p,selected)
    recs = [{'ticker':s['ticker'],'allocation':w,'match_score':match_score(p,s),'reason':f"성장 선호도 {p.growth_preference:g}점과 종목 성장 점수 {s['growth_score']:g}점, 손실 민감도 {p.loss_sensitivity:g}점을 함께 비교했습니다. 변동성 {s['volatility']:g}점과 최대 낙폭 위험 {s['max_drawdown']:g}점을 반영해 비중을 {w}%로 정했습니다."} for s,w in zip(selected,weights)]
    result = Portfolio(portfolio_summary='설문 성향과 종목의 위험·성장·안정성을 비교해 세 종목을 조합했습니다. 변동성과 최대 낙폭 위험을 반영하고, 최소 두 업종에 나누어 비중을 배정했습니다. 가상 데이터에 기반한 교육용 예시입니다.',recommendations=recs)
    return validate_selection(result,p,stocks)

def fallback_options(p,stocks):
    options = []
    excluded = set()
    for _ in range(3):
        option = fallback_portfolio(p,stocks,excluded)
        options.append(option)
        excluded.add(tuple(sorted(r.ticker for r in option.recommendations)))
    return PortfolioOptions(portfolios=options)

def validate_options(result,p,stocks):
    result = PortfolioOptions.model_validate(result.model_dump())
    for option in result.portfolios:
        validate_selection(option,p,stocks)
    return result

def recommend_portfolio(p,stocks):
    if api_enabled():
        try:
            result = structured_call(SYSTEM_PROMPT,{'USER PROFILE':p.model_dump(exclude={'summary'}),'STOCK DATA':stocks,'risk_limit':risk_limit(p)},PortfolioOptions)
            return validate_options(result,p,stocks),'ai'
        except RECOVERABLE as exc:
            report_fallback('portfolio',exc)
    return fallback_options(p,stocks),'fallback'
