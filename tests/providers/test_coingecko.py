import pytest
from src.providers.coingecko import api_coingecko_contract, api_coingecko_coin_data

# Known contract and coin for testing
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
BITCOIN_ID = "bitcoin"

def test_api_coingecko_contract():
    """Test that we can fetch contract data from CoinGecko."""
    result = api_coingecko_contract.invoke({"address": USDC_CONTRACT})
    assert isinstance(result, dict)
    assert "symbol" in result
    assert result["symbol"].lower() == "usdc"
    assert "market_cap_usd" in result

def test_api_coingecko_coin_data():
    """Test that we can fetch coin data from CoinGecko."""
    result = api_coingecko_coin_data.invoke({"coin_id": BITCOIN_ID})
    assert isinstance(result, dict)
    assert "symbol" in result
    assert result["symbol"].lower() == "btc"
    assert "market_cap_rank" in result
