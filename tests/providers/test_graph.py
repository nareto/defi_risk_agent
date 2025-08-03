import pytest
from src.providers.graph import (
    api_graph_aave_account_summary,
    api_graph_aave_liquidations,
)

# Vitalik's wallet – highly active and has Aave interactions historically
TEST_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

def test_api_graph_aave_account_summary():
    """Basic smoke-test: sub-graph call returns a mapping with required keys."""
    result = api_graph_aave_account_summary.invoke({"wallet_address": TEST_ADDRESS})
    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "totalCollateralUSD",
        "totalDebtUSD",
        "liquidationThreshold",
    }
    # We only assert types to avoid flakiness caused by market moves.
    assert isinstance(result["totalCollateralUSD"], (int, float))
    assert isinstance(result["totalDebtUSD"], (int, float))
    assert isinstance(result["liquidationThreshold"], (int, float))
    assert 0 <= result["liquidationThreshold"] <= 1


def test_api_graph_aave_liquidations():
    """Ensure the endpoint responds and returns a list (possibly empty)."""
    result = api_graph_aave_liquidations.invoke({"wallet_address": TEST_ADDRESS, "max_pages": 1})
    assert isinstance(result, list)
    if result:  # Only check structure if events exist
        assert "timestamp" in result[0]
        assert "id" in result[0]
