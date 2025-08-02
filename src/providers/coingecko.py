import requests, decimal
import datetime as dt


def get_token_marketcap_and_rank(address, chain="ethereum"):
    # https://docs.coingecko.com/reference/coins-contract-address
    url = f"https://api.coingecko.com/api/v3/coins/{chain}/contract/{address}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    market_cap = decimal.Decimal(data["market_data"]["market_cap"]["usd"])
    rank = data["market_cap_rank"]  # may be None for tiny tokens
    return {
        "symbol": data["symbol"],
        "market_cap_usd": market_cap,
        "market_cap_rank": rank,
    }


def get_coin_marketcap_and_rank(coin_id):
    # https://docs.coingecko.com/reference/coins-id
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    market_cap = decimal.Decimal(data["market_data"]["market_cap"]["usd"])
    rank = data["market_cap_rank"]
    return {
        "symbol": data["symbol"],
        "market_cap_usd": market_cap,
        "market_cap_rank": rank,
        "genesis_date": dt.datetime.combine(
            dt.date.fromisoformat(data["genesis_date"]), dt.datetime.min.time()
        ).isoformat(),
    }
