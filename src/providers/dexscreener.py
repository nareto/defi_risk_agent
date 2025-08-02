import requests
from langchain_core.tools import tool
from src.utils import rate_limit

@rate_limit(max_calls=2, period_seconds=10)
@tool
def api_dexscreener_token_data(network: str, token_addresses: str):
    """
    Fetches token information from DexScreener API.
    `network`: e.g., 'ethereum', 'bsc'
    `token_addresses`: comma-separated token addresses
    """
    url = f"https://api.dexscreener.com/v1/latest/tokens/{token_addresses}"
    
    response = requests.get(url, headers={"Accept": "*/*"}, timeout=15)
    response.raise_for_status()
    data =  response.json()
    # [{'chainId': 'ethereum',
    #   'dexId': 'uniswap',
    #   'url': 'https://dexscreener.com/ethereum/0x0890f93a1fd344b3437ec10c1c14d1a581142c5f',
    #   'pairAddress': '0x0890f93A1fd344B3437Ec10c1C14d1a581142c5f',
    #   'labels': ['v2'],
    #   'baseToken': {'address': '0x3fC29836E84E471a053D2D9E80494A867D670EAD',
    #    'name': 'Ethereum Games',
    #    'symbol': 'ETHG'},
    #   'quoteToken': {'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    #    'name': 'Wrapped Ether',
    #    'symbol': 'WETH'},
    #   'priceNative': '0.0001237',
    #   'priceUsd': '0.4326',
    #   'txns': {'m5': {'buys': 0, 'sells': 0},
    #    'h1': {'buys': 0, 'sells': 1},
    #    'h6': {'buys': 0, 'sells': 1},
    #    'h24': {'buys': 0, 'sells': 1}},
    #   'volume': {'h24': 1699.09, 'h6': 1699.09, 'h1': 1699.09, 'm5': 0},
    #   'priceChange': {},
    #   'liquidity': {'usd': 74768.45, 'base': 86414, 'quote': 10.698},
    #   'pairCreatedAt': 1719047087000}]
    # return {
    #     'symbol'@ data['quoteToken']['']
    # }
    return data

