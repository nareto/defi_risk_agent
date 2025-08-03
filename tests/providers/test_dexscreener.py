import pytest
from src.providers.dexscreener import api_dexscreener_token_data

# Known token address for testing
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

def test_api_dexscreener_token_data():
    """Test that we can fetch token data from DexScreener."""
    result = api_dexscreener_token_data.invoke({
        "network": "ethereum",
        "token_addresses": WETH_ADDRESS
    })
    assert isinstance(result, list)
    assert "pairAddress" in result[0]
    assert result[0]["baseToken"]["symbol"] == "WETH"
