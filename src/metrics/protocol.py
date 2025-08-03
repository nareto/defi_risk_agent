from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List

class ProtocolPosition(BaseModel):
    """Represents a single position in a DeFi protocol."""
    protocol_name: str
    usd_value: float
    protocol_tvl_usd: float = Field(description="Total Value Locked of the protocol in USD.")

class LowTvlProtocolInput(BaseModel):
    """Input for calculating exposure to low-TVL protocols."""
    positions: List[ProtocolPosition]
    tvl_threshold_usd: float = Field(default=5_000_000, description="The TVL threshold below which a protocol is considered low-TVL.")

class LowTvlProtocolOutput(BaseModel):
    """Output for the Low-TVL Protocol Concentration metric."""
    metric_name: str = "Low-TVL Protocol Concentration"
    percentage_exposure: float
    description: str

@tool
def metric_calculate_low_tvl_protocol_concentration(
    data: LowTvlProtocolInput,
) -> LowTvlProtocolOutput:
    """
    Calculates the percentage of wallet assets in protocols with TVL below a threshold.
    """
    total_value = sum(p.usd_value for p in data.positions)
    if total_value == 0:
        return LowTvlProtocolOutput(
            percentage_exposure=0,
            description="Wallet has no assets in DeFi protocols."
        )

    low_tvl_value = sum(
        p.usd_value for p in data.positions if p.protocol_tvl_usd < data.tvl_threshold_usd
    )

    percentage = (low_tvl_value / total_value) * 100 if total_value > 0 else 0
    
    description = (
        f"{percentage:.2f}% of assets are in protocols with less than "
        f"${data.tvl_threshold_usd:,.0f} TVL."
    )

    return LowTvlProtocolOutput(
        percentage_exposure=percentage,
        description=description,
    )
