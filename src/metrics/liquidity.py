from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List

class ExoticAsset(BaseModel):
    symbol: str
    usd_value: float
    market_cap_rank: int | None = Field(description="None if unranked")


class ExoticAssetExposureInput(BaseModel):
    assets: List[ExoticAsset]


class ExoticAssetExposureOutput(BaseModel):
    metric_name: str = "Exotic & Unproven Asset Exposure"
    percentage_exposure: float
    description: str


class PortfolioConcentrationInput(BaseModel):
    asset_values: List[float]


class PortfolioConcentrationOutput(BaseModel):
    metric_name: str = "Portfolio Concentration Index (HHI)"
    hhi_score: float


@tool
def metric_calculate_exotic_asset_exposure(
    data: ExoticAssetExposureInput,
) -> ExoticAssetExposureOutput:
    """Percent USD in assets ranked >200 or unranked."""
    total = sum(a.usd_value for a in data.assets)
    if total == 0:
        return ExoticAssetExposureOutput(percentage_exposure=0, description="Wallet empty")
    exotic_val = sum(
        a.usd_value for a in data.assets if a.market_cap_rank is None or a.market_cap_rank > 200
    )
    pct = exotic_val / total * 100
    return ExoticAssetExposureOutput(
        percentage_exposure=pct,
        description=f"{pct:.2f}% of value in assets ranked >200 or unranked.",
    )


@tool
def metric_calculate_portfolio_concentration(
    data: PortfolioConcentrationInput,
) -> PortfolioConcentrationOutput:
    """Compute the Herfindahl-Hirschman Index (0 diversified → 1 concentrated)."""
    total = sum(data.asset_values)
    if total == 0:
        return PortfolioConcentrationOutput(hhi_score=0)
    hhi = sum((v / total) ** 2 for v in data.asset_values)
    return PortfolioConcentrationOutput(hhi_score=hhi)
