import pytest
from src.providers.goplus import api_goplus_token_security

# Known token address for testing
USDC_ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

def test_api_goplus_token_security():
    """Test that we can fetch token security data from GoPlus."""
    result = api_goplus_token_security.invoke({"address": USDC_ADDRESS})
    assert isinstance(result, dict)
    assert "result" in result
    assert USDC_ADDRESS.lower() in result["result"]
    assert "is_open_source" in result["result"][USDC_ADDRESS.lower()]
