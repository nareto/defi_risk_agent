from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List

from src.metrics.base import BaseMetricOutput

class BridgedAsset(BaseModel):
    """Represents a single asset and its bridged status."""
    symbol: str
    usd_value: float
    is_bridged: bool = Field(description="True if the asset is a bridged (non-native) version.")

class BridgedAssetExposureInput(BaseModel):
    """Input for the Bridged Asset Exposure metric."""
    assets: List[BridgedAsset]

class BridgedAssetExposureOutput(BaseMetricOutput):
    metric_name: str = "Bridged Asset Exposure"
    metric_description: str = "The percentage of the wallet's total value that is held in bridged (non-native) assets."

    percentage_exposure: float

    @property
    def value(self) -> float:
        return self.percentage_exposure

@tool
def metric_calculate_bridged_asset_exposure(
    data: BridgedAssetExposureInput,
) -> BridgedAssetExposureOutput:
    """
    Calculates the percentage of the wallet's total value held in bridged (non-native) assets.
    """
    total_value = sum(a.usd_value for a in data.assets)
    if total_value == 0:
        return BridgedAssetExposureOutput(
            percentage_exposure=0,
            value_explanation="Wallet has no assets."
        )

    bridged_value = sum(a.usd_value for a in data.assets if a.is_bridged)

    percentage = (bridged_value / total_value) * 100 if total_value > 0 else 0
    
    explanation = f"{percentage:.2f}% of the portfolio's value is held in bridged (non-native) assets."

    return BridgedAssetExposureOutput(
        percentage_exposure=percentage,
        value_explanation=explanation,
    )
