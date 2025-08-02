# %%

import os, requests, pprint
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["ALCHEMY_API_KEY"]

import os, decimal, requests, pprint
from decimal import Decimal

API = os.environ["ALCHEMY_API_KEY"]
BASE = f"https://api.g.alchemy.com/data/v1/{API}"


def get_portfolio(addr, network="eth-mainnet"):
    url = f"{BASE}/assets/tokens/by-address"
    body = {
        "addresses": [{"address": addr, "networks": [network]}],
        "withMetadata": True,
        "withPrices": True,
        "includeNativeTokens": True,
        "includeErc20Tokens": True,
    }
    # {
    #   "data": {
    #     "tokens": [
    #       {
    #         "address": "0x1e6e8695fab3eb382534915ea8d7cc1d1994b152",
    #         "network": "eth-mainnet",
    #         "tokenAddress": null,
    #         "tokenBalance": "0x00000000000000000000000000000000000000000000000009cbebbc25efff3c",
    #         "tokenMetadata": {
    #           "symbol": null,
    #           "decimals": null,
    #           "name": null,
    #           "logo": null
    #         },
    #         "tokenPrices": [
    #           {
    #             "currency": "usd",
    #             "value": "3510.8599871765",
    #             "lastUpdatedAt": "2025-08-02T07: 50: 44Z"
    #           }
    #         ]
    #       },
    #       {
    #         "address": "0x1e6e8695fab3eb382534915ea8d7cc1d1994b152",
    #         "network": "eth-mainnet",
    #         "tokenAddress": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    #         "tokenBalance": "0x00000000000000000000000000000000000000000000000000000000017ab20c",
    #         "tokenMetadata": {
    #           "decimals": 6,
    #           "logo": "https: //static.alchemyapi.io/images/assets/3408.png",
    #           "name": "USDC",
    #           "symbol": "USDC"
    #         },
    #         "tokenPrices": [
    #           {
    #             "currency": "usd",
    #             "value": "0.989741524857",
    #             "lastUpdatedAt": "2025-08-02T07: 51: 05.016508806Z"
    #           }
    #         ]
    #       },
    #       {
    #         "address": "0x1e6e8695fab3eb382534915ea8d7cc1d1994b152",
    #         "network": "eth-mainnet",
    #         "tokenAddress": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    #         "tokenBalance": "0x0000000000000000000000000000000000000000000000000000000000000000",
    #         "tokenMetadata": {
    #           "decimals": 18,
    #           "logo": "https: //static.alchemyapi.io/images/assets/2396.png",
    #           "name": "WETH",
    #           "symbol": "WETH"
    #         },
    #         "tokenPrices": [
    #           {
    #             "currency": "usd",
    #             "value": "3525.70780416807",
    #             "lastUpdatedAt": "2025-08-02T07: 51: 19.155535972Z"
    #           }
    #         ]
    #       }
    #     ],
    #     "pageKey": null
    #   }
    # }
    tokens = requests.post(url, json=body, timeout=30).json()["data"]["tokens"]
    clean = []
    for t in tokens:
        bal_hex = t["tokenBalance"]
        raw = int(bal_hex, 16)  # ① hex → int
        decs = t["tokenMetadata"].get("decimals") or 18  # ② scale
        human = Decimal(raw) / (10 ** int(decs))

        # pick the first USD quote if it exists
        price_rows = [p for p in t["tokenPrices"] if p["currency"].lower() == "usd"]
        price = Decimal(price_rows[0]["value"]) if price_rows else Decimal(0)

        if t["tokenAddress"] is None:
            symbol = "ETH"
        else:
            symbol = t["tokenMetadata"].get("symbol")
        clean.append(
            {
                "token_address": t['tokenAddress'],
                "symbol": symbol,
                "balance": human,
                "usd_price": price,
                "usd_value": human * price,
            }
        )

    return sorted(clean, key=lambda x: x["usd_value"], reverse=True)


def get_history(address, network="eth-mainnet", limit=50, after=None):
    """Fetch one page of historical tx; pass `after` to page forward."""
    url = f"{BASE}/transactions/history/by-address"
    payload = {
        "addresses": [{"address": address, "networks": [network]}],
        "limit": limit,
    }
    if after:  # cursor from previous response
        payload["after"] = after
    return requests.post(url, json=payload, timeout=30).json()
