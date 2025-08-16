from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List
import datetime as dt

from src.metrics.base import BaseMetricOutput

class Transaction(BaseModel):
    """Represents a single outgoing transaction from a wallet."""
    timestamp: dt.datetime
    usd_value: float = Field(description="The USD value of the assets transferred or swapped out.")

class PortfolioChurnRateInput(BaseModel):
    """Input for the Portfolio Churn Rate metric."""
    outgoing_transactions: List[Transaction]
    start_period_value_usd: float
    end_period_value_usd: float
    period_days: int = Field(default=30, description="The time window for the analysis in days.")

class PortfolioChurnRateOutput(BaseMetricOutput):
    """Output for the Portfolio Churn Rate metric."""
    metric_name: str = "Portfolio Churn Rate"
    metric_description: str = "The value of assets swapped or transferred out over a period, calculated as a percentage of the wallet's average total value."

    churn_rate_percentage: float

    @property
    def value(self) -> float:
        return self.churn_rate_percentage

@tool
def metric_calculate_portfolio_churn_rate(
    data: PortfolioChurnRateInput,
) -> PortfolioChurnRateOutput:
    """
    Calculates the value of assets swapped or transferred out as a percentage of 
    the wallet's average total value over a period.
    """
    total_outgoing_value = sum(t.usd_value for t in data.outgoing_transactions)

    # Calculate the average wallet value over the period
    average_wallet_value = (data.start_period_value_usd + data.end_period_value_usd) / 2

    if average_wallet_value == 0:
        churn_rate = 0.0
    else:
        # Annualize the churn rate
        churn_rate = (total_outgoing_value / average_wallet_value) * (365 / data.period_days) * 100

    explanation = (
        f"The wallet's annualized churn rate over the last {data.period_days} days "
        f"is {churn_rate:.2f}%. This represents the percentage of the average portfolio value "
        f"that is traded or transferred out annually."
    )

    return PortfolioChurnRateOutput(
        churn_rate_percentage=churn_rate,
        value_explanation=explanation,
    )
