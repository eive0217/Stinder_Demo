from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

class InvestorProfile(StrictModel):
    risk_tolerance: float = Field(ge=0, le=10)
    growth_preference: float = Field(ge=0, le=10)
    time_horizon: float = Field(ge=0, le=10)
    loss_sensitivity: float = Field(ge=0, le=10)
    investor_type: Literal['steady_planner','balanced_builder','growth_seeker','bold_explorer']
    summary: str = Field(min_length=1, max_length=1200)

class Recommendation(StrictModel):
    ticker: str = Field(min_length=1)
    allocation: int = Field(ge=15, le=50)
    match_score: float = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=1500)

class Portfolio(StrictModel):
    portfolio_summary: str = Field(min_length=1, max_length=2000)
    recommendations: list[Recommendation] = Field(min_length=3, max_length=3)

    @model_validator(mode='after')
    def validate_portfolio(self):
        if sum(r.allocation for r in self.recommendations) != 100:
            raise ValueError('비중 합계는 100이어야 합니다.')
        if len({r.ticker for r in self.recommendations}) != 3:
            raise ValueError('서로 다른 3개 종목이 필요합니다.')
        return self

class ETF(StrictModel):
    ticker: str = Field(min_length=1)
    fund_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    risk_score: float = Field(ge=0, le=10)
    growth_score: float = Field(ge=0, le=10)
    stability_score: float = Field(ge=0, le=10)
    liquidity_score: float = Field(ge=0, le=10)
    volatility: float = Field(ge=0, le=10)
    max_drawdown: float = Field(ge=0, le=10)
    issuer: str = Field(min_length=1)
    exposure: str = Field(min_length=1)
    overlap_group: str = Field(min_length=1)
    expense_ratio: float = Field(ge=0, le=5)
    listing_country: Literal['US']
    data_kind: Literal['synthetic']

class PortfolioOptions(StrictModel):
    portfolios: list[Portfolio] = Field(min_length=3, max_length=3)

    @model_validator(mode='after')
    def distinct_options(self):
        signatures = [tuple(sorted(r.ticker for r in p.recommendations)) for p in self.portfolios]
        if len(set(signatures)) != 3:
            raise ValueError('추천안별 종목 조합이 달라야 합니다.')
        return self
