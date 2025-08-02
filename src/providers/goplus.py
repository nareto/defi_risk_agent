
import requests
from langchain_core.tools import tool
from src.utils import rate_limit

@rate_limit(max_calls=2, period_seconds=10)
@tool
def api_goplus_token_security(address: str, chain_id: int = 1):
    """
    Fetches token security data from GoPlus API.
    `address`: the contract address to get security info about.
    `chain_id`: 1 for Ethereum, 56 for BSC, etc.
    """
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}"
    params = {"contract_addresses": address.lower()}
    
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data
    
    # # The result is a dictionary keyed by the lowercase address.
    # token_info = data.get("result", {}).get(address.lower())
    # if not token_info:
    #     return {}
    
    # # Extract all security flags (e.g., is_open_source, is_honeypot).
    # flags = {k: v for k, v in token_info.items() if k.startswith("is_")}
    # return flags

