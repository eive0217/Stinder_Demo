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

class Stock(StrictModel):
    ticker: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    sector: str = Field(min_length=1)
    risk_score: float = Field(ge=0, le=10)
    growth_score: float = Field(ge=0, le=10)
    stability_score: float = Field(ge=0, le=10)
    analyst_confidence: float = Field(ge=0, le=10)
    expected_upside: float = Field(ge=-100, le=1000)
    volatility: float = Field(ge=0, le=10)
    max_drawdown: float = Field(ge=0, le=10)
    analyst_consensus: Literal['매수','중립','매도']
    average_price_target: float = Field(gt=0)
    low_price_target: float = Field(gt=0)
    high_price_target: float = Field(gt=0)

    @model_validator(mode='after')
    def ordered_targets(self):
        if not self.low_price_target <= self.average_price_target <= self.high_price_target:
            raise ValueError('목표가 순서 오류')
        return self
