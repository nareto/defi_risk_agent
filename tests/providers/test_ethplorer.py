import pytest
from src.providers.ethplorer import api_ethplorer_token_data

# Known token address for testing
USDC_ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

def test_api_ethplorer_token_data():
    """Test that we can fetch token data from Ethplorer."""
    result = api_ethplorer_token_data.invoke({"address": USDC_ADDRESS})
    assert isinstance(result, dict)
    assert "address" in result
    assert result["address"] == USDC_ADDRESS.lower()
    assert "name" in result
    assert result["name"] == "USD Coin"
