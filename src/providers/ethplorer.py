import requests
import datetime as dt
from decimal import Decimal
from langchain_core.tools import tool
from src.utils import rate_limit


@rate_limit(max_calls=2, period_seconds=10)
@tool
def api_ethplorer_token_data(address: str):
    """Fetch token data for the contract address"""
    out = requests.get(
        f"https://api.ethplorer.io/getTokenInfo/{address}?apiKey=freekey"
    ).json()
    return out
    # {
    #   "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    #   "decimals": "6",
    #   "lastUpdated": 1754125148,
    #   "name": "USD Coin",
    #   "owner": "0xfcb19e6a322b27c06842a71e8c725399f049ae3a",
    #   "contractInfo": {
    #     "creatorAddress": "0x95ba4cf87d6723ad9c0db21737d862be80e93911",
    #     "creationTransactionHash": "0xe7e0fe390354509cd08c9a0168536938600ddc552b3f7cb96030ebef62e75895",
    #     "creationTimestamp": 1533324504
    #   },
    #   "price": {
    #     "rate": 0.9999547891304532,
    #     "diff": -0.01,
    #     "diff7d": -0.01,
    #     "ts": 1754124960,
    #     "marketCapUsd": 64238974891.81964,
    #     "availableSupply": 64241879323.04516,
    #     "volume24h": 15794140984.739344,
    #     "volDiff1": 2.251006597468816,
    #     "volDiff7": -2.328378148314087,
    #     "volDiff30": 49.23897549646233,
    #     "diff30d": 0.0010173459515243621,
    #     "currency": "USD"
    #   },
    #   "symbol": "USDC",
    #   "totalSupply": "41962492661685937",
    #   "transfersCount": 155637104,
    #   "txsCount": 66015390,
    #   "issuancesCount": 1608408,
    #   "holdersCount": 3601712,
    #   "image": "/images/usdc.png",
    #   "ethTransfersCount": 0,
    #   "countOps": 155637104
    # }
    # return {
    #     "symbol": out["symbol"],
    #     "market_cap_usd": Decimal(str(out["price"]["marketCapUsd"])),
    #     "creation_date_isoformat": dt.datetime.fromtimestamp(
    #         out["contractInfo"]["creationTimestamp"]
    #     ).isoformat(),
    # }
