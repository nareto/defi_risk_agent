from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Annotated


# ───────────────────────────────────────────────────────────────
# 1. Loan-to-Value  (LTV) / Health-Factor
# ───────────────────────────────────────────────────────────────
class LTVInput(BaseModel):
    total_debt_usd: float = Field(..., description="Sum of all outstanding debt in USD.")
    total_collateral_usd: float = Field(..., description="Current USD value of supplied collateral.")
    liquidation_threshold: float = Field(
        0.85,
        description=(
            "Maximum LTV the lending protocol allows before liquidation (e.g. 0.85 -> 85%). "
            "If unknown, supply a protocol default or leave at 0.85."
        ),
    )


class LTVOutput(BaseModel):
    metric_name: str = "Loan-to-Value (LTV) / Health-Factor"
    ltv_ratio: float = Field(..., description="Current LTV = debt / collateral (0-1).")
    health_factor: float | None = Field(
        None,
        description=(
            "Simple inverse of utilisation: HF = liquidation_threshold / LTV. "
            "Higher is safer; undefined if collateral is zero."
        ),
    )
    description: str


@tool
def metric_calculate_ltv(data: LTVInput) -> LTVOutput:
    """Compute current Loan-to-Value ratio and a simplified health factor."""
    if data.total_collateral_usd <= 0:
        return LTVOutput(
            ltv_ratio=1.0,
            health_factor=None,
            description="No collateral supplied; position assumed fully risky (LTV = 100%).",
        )

    ltv = data.total_debt_usd / data.total_collateral_usd
    hf = (data.liquidation_threshold / ltv) if ltv > 0 else float("inf")
    return LTVOutput(
        ltv_ratio=ltv,
        health_factor=hf,
        description=f"LTV = {ltv:.2%}. Health-Factor ≈ {hf:.2f}.",
    )


# ───────────────────────────────────────────────────────────────
# 2. Liquidation Distance  (Δₗᵢq)
# ───────────────────────────────────────────────────────────────
class LiquidationDistanceInput(BaseModel):
    current_ltv: float = Field(..., description="Current LTV ratio (0-1).")
    liquidation_threshold: float = Field(..., description="Protocol liquidation threshold (0-1).")


class LiquidationDistanceOutput(BaseModel):
    metric_name: str = "Liquidation Distance (Δₗᵢq)"
    distance_percent: float = Field(..., description="Percent price drop of collateral that triggers liquidation.")
    description: str


@tool
def metric_calculate_liquidation_distance(
    data: LiquidationDistanceInput,
) -> LiquidationDistanceOutput:
    """
    Distance = 1 – (current_ltv / liquidation_threshold)
    Interpreted as the % drop in collateral value that would push LTV to the threshold.
    """
    if data.liquidation_threshold <= 0:
        return LiquidationDistanceOutput(
            distance_percent=0.0,
            description="Invalid liquidation threshold; distance undefined.",
        )

    util = data.current_ltv / data.liquidation_threshold
    distance = max(0.0, 1 - util) * 100  # expressed in %
    return LiquidationDistanceOutput(
        distance_percent=distance,
        description=f"Collateral can fall {distance:.2f}% before liquidation.",
    )


# ───────────────────────────────────────────────────────────────
# 3. Historical Liquidation Events
# ───────────────────────────────────────────────────────────────
class LiquidationHistoryInput(BaseModel):
    liquidation_event_timestamps: List[int] = Field(
        ..., description="Unix timestamps (or block numbers) of past liquidations."
    )


class LiquidationHistoryOutput(BaseModel):
    metric_name: str = "Historical Liquidation Events"
    total_events: int
    most_recent_days_ago: int | None = Field(
        None, description="Days since the most recent liquidation event."
    )
    description: str


@tool
def metric_calculate_liquidation_history(
    data: LiquidationHistoryInput,
) -> LiquidationHistoryOutput:
    """Count past liquidation events and find recency."""
    events = len(data.liquidation_event_timestamps)
    if events == 0:
        return LiquidationHistoryOutput(
            total_events=0,
            most_recent_days_ago=None,
            description="No recorded liquidation events.",
        )

    # Very lightweight time-delta calc (assumes timestamps are UNIX seconds)
    import time

    now = int(time.time())
    most_recent_secs = now - max(data.liquidation_event_timestamps)
    days_ago = int(most_recent_secs // 86_400)

    return LiquidationHistoryOutput(
        total_events=events,
        most_recent_days_ago=days_ago,
        description=f"{events} liquidation events; last occurred {days_ago} days ago.",
    )