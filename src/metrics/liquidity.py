from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List
from typing import Annotated  
from .base import BaseMetricOutput

class ExoticAsset(BaseModel):
    symbol: str
    usd_value: float
    market_cap_rank: int | None = Field(description="None if unranked")


class ExoticAssetExposureInput(BaseModel):
    assets: List[ExoticAsset]



class ExoticAssetExposureOutput(BaseMetricOutput):
    metric_name: str = "Exotic Asset Exposure"
    description: str = "The percentage of a wallet's value held in assets that are outside the top 100–200 by market capitalization or have a very short history."

    percentage_exposure: float

    @property
    def value(self) -> float: 
        return self.percentage_exposure



class PortfolioConcentrationInput(BaseModel):
    asset_values: List[float]


class PortfolioConcentrationOutput(BaseMetricOutput):
    metric_name: str = "Portfolio Concentration Index (HHI)"
    description: str = "Calculated on the wallet's holdings to measure diversification. A score near 100 signifies high concentration in a single asset."
    
    hhi_score: float

    @property
    def value(self) -> float: 
        return self.hhi_score

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
    """Compute the Herfindahl-Hirschman Index (0 diversified → 100 concentrated)."""
    total = sum(data.asset_values)
    if total == 0:
        return PortfolioConcentrationOutput(hhi_score=0)
    hhi = 100*sum((v / total) ** 2 for v in data.asset_values)
    return PortfolioConcentrationOutput(hhi_score=hhi)
