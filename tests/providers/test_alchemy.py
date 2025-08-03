import pytest
from src.providers.alchemy import api_alchemy_portfolio, api_alchemy_tx_history

# A known address with activity
TEST_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # vitalik.eth

def test_api_alchemy_portfolio():
    """Test that we can fetch a portfolio from Alchemy."""
    result = api_alchemy_portfolio.invoke({"address": TEST_ADDRESS})
    assert isinstance(result, dict)
    assert "data" in result
    assert "tokens" in result["data"]
    assert len(result["data"]["tokens"]) > 0

def test_api_alchemy_tx_history():
    """Test that we can fetch transaction history from Alchemy."""
    result = api_alchemy_tx_history.invoke({"address": TEST_ADDRESS, "limit": 5})
    assert isinstance(result, dict)
    assert "transactions" in result
    assert len(result["transactions"]) == 5
