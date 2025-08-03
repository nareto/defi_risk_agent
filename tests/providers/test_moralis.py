import pytest
from src.providers.moralis import (
    api_moralis_wallet_portfolio,
    api_moralis_wallet_history,
)

TEST_ADDRESS = "0xcB1C1FdE09f811B294172696404e88E658659905"


def test_api_moralis_wallet_portfolio():
    """Test that we can fetch a wallet portfolio from Moralis."""
    result = api_moralis_wallet_portfolio.invoke({"address": TEST_ADDRESS})
    assert isinstance(result, list)
    assert len(result) > 0
    assert "token_address" in result[0]


def test_api_moralis_wallet_history():
    """Test that we can fetch wallet history from Moralis."""
    result = api_moralis_wallet_history.invoke(
        {"address": TEST_ADDRESS, "page_size": 5}
    )
    assert isinstance(result, dict)
    assert "result" in result
    assert "hash" in result["result"][0]
