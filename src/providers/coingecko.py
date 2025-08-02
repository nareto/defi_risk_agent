import datetime as dt
import decimal

import requests
from langchain_core.tools import tool


@tool
def api_coingecko_contract(address: str, chain: str = "ethereum"):
    """Fetch data on contract https://docs.coingecko.com/reference/coins-contract-address. Example response (curated):
    {
    "id": "usd-coin",
    "symbol": "usdc",
    "name": "USDC",
    "web_slug": "usdc",
    "asset_platform_id": "ethereum",
    "platforms": {
        "ethereum": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "polkadot": "1337",
        //...
    },
    "detail_platforms": {
        "ethereum": {
        "decimal_place": 6,
        "contract_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        },
        "polkadot": {
        "decimal_place": 6,
        "contract_address": "1337"
        },
        //...
    },
    "block_time_in_minutes": 0,
    "hashing_algorithm": null,
    "categories": [
        "Ronin Ecosystem",
        "Osmosis Ecosystem",
        //...
    ],
    "preview_listing": false,
    "public_notice": "USD Coin (USDC) has rebranded to USDC (USDC). For more information, please refer to this <a href=\"https://www.circle.com/blog/usd-coin-and-euro-coin-are-now-exclusively-usdc-and-eurc\">announcement</a> from the Circle Blog.",
    "additional_notices": [],
    "localization": {
        "en": "USDC",
        "de": "USDC",
        //...
    },
    "description": {
        "en": "USDC is a fully collateralized US dollar stablecoin ...",
        "de": "USDC is a fully collateralized US dollar stablecoin..."
    },
    "links": {
        "homepage": [
        "https://www.circle.com/en/usdc",
        //...
    },
    "image": {
        "thumb": "https://assets.coingecko.com/coins/images/6319/thumb/usdc.png?1696506694",
        "small": "https://assets.coingecko.com/coins/images/6319/small/usdc.png?1696506694",
        "large": "https://assets.coingecko.com/coins/images/6319/large/usdc.png?1696506694"
    },
    "country_origin": "US",
    "genesis_date": null,
    "contract_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "sentiment_votes_up_percentage": 33.33,
    "sentiment_votes_down_percentage": 66.67,
    "watchlist_portfolio_users": 126374,
    "market_cap_rank": 7,
    "market_data": {
        "current_price": {
        "aed": 3.68,
        "ars": 863.06,
        //...
        },
        "total_value_locked": null,
        "mcap_to_tvl_ratio": null,
        "fdv_to_tvl_ratio": null,
        "roi": null,
        "ath": {
        "aed": 4.31,
        "ars": 868.65,
        //...
        },
        "ath_change_percentage": {
        "aed": -14.38389,
        "ars": -0.51451,
        //...
        },
        //...
        "total_supply": 32937454819.1184,
        "max_supply": null,
        "circulating_supply": 32936427353.685,
        "last_updated": "2024-04-07T16:35:22.339Z"
    },
        //...
        "trust_score": "green",
        "bid_ask_spread_percentage": 0.010001,
        "timestamp": "2024-04-07T15:34:49+00:00",
        "last_traded_at": "2024-04-07T15:34:49+00:00",
        "last_fetch_at": "2024-04-07T15:34:49+00:00",
        "is_anomaly": false,
        "is_stale": false,
        "trade_url": "https://www.bitunix.com/spot-trade?symbol=USDCUSDT",
        "token_info_url": null,
        "coin_id": "usd-coin",
        "target_coin_id": "tether"
        }
    ]
    }
    """

    url = f"https://api.coingecko.com/api/v3/coins/{chain}/contract/{address}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
    }
    r = requests.get(url, params=params, timeout=20)
    return r.json()
    # r.raise_for_status()
    # data = r.json()

    # market_cap = decimal.Decimal(data["market_data"]["market_cap"]["usd"])
    # rank = data["market_cap_rank"]  # may be None for tiny tokens
    # return {
    #     "symbol": data["symbol"],
    #     "market_cap_usd": market_cap,
    #     "market_cap_rank": rank,
    # }


@tool
def api_coingecko_coin_data(coin_id):
    """Fetch data for coin https://docs.coingecko.com/reference/coins-id. Example response (curated):
        {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "web_slug": "bitcoin",
    "asset_platform_id": null,
    "platforms": {
        "": ""
    },
    "detail_platforms": {
        "": {
        "decimal_place": null,
        "contract_address": ""
        }
    },
    "block_time_in_minutes": 10,
    "hashing_algorithm": "SHA-256",
    "categories": [
        "FTX Holdings",
        "Cryptocurrency",
        "Proof of Work (PoW)",
        "Layer 1 (L1)"
    ],
    "preview_listing": false,
    "public_notice": null,
    "additional_notices": [],
    "localization": {
        "en": "Bitcoin",
        "de": "Bitcoin"
    },
    "description": {
        "en": "Bitcoin is the first successful internet money based on peer-to-peer technology...</a>.",
        "de": ""
    },
    "links": {
        "homepage": [
        "http://www.bitcoin.org",
        "",
        ""
        ],
        "whitepaper": "https://bitcoin.org/bitcoin.pdf",
        "blockchain_site": [
        "https://mempool.space/",
        "https://blockchair.com/bitcoin/",
        "https://btc.com/",
        "https://btc.tokenview.io/",
        "https://www.oklink.com/btc",
        "https://3xpl.com/bitcoin"
        ],
        "official_forum_url": [
        "https://bitcointalk.org/"
        ],
        "chat_url": [
        ""
        ],
        "announcement_url": [
        "",
        ""
        ],
        "snapshot_url": null,
        "twitter_screen_name": "bitcoin",
        "facebook_username": "bitcoins",
        "bitcointalk_thread_identifier": null,
        "telegram_channel_identifier": "",
        "subreddit_url": "https://www.reddit.com/r/Bitcoin/",
        "repos_url": {
        "github": [
            "https://github.com/bitcoin/bitcoin",
            "https://github.com/bitcoin/bips"
        ],
        "bitbucket": []
        }
    },
    "image": {
        "thumb": "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png?1696501400",
        "small": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png?1696501400",
        "large": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png?1696501400"
    },
    "country_origin": "",
    "genesis_date": "2009-01-03",
    "sentiment_votes_up_percentage": 84.07,
    "sentiment_votes_down_percentage": 15.93,
    "watchlist_portfolio_users": 1541900,
    "market_cap_rank": 1,
    "market_data": {
        "current_price": {
        //...
        "total_supply": 21000000,
        "max_supply": 21000000,
        "circulating_supply": 19675962,
        "last_updated": "2024-04-07T15:24:51.021Z"
        //...
    "status_updates": [],
    "last_updated": "2024-04-07T15:24:51.021Z",
    "tickers": [
        {
        "base": "BTC",
        "target": "USDT",
        "market": {
            "name": "Binance",
            "identifier": "binance",
            "has_trading_incentive": false
        },
        "last": 69816,
        "volume": 19988.82111,
        "converted_last": {
            "btc": 0.99999255,
            "eth": 20.441016,
            "usd": 69835
        },
        "converted_volume": {
            "btc": 19783,
            "eth": 404380,
            "usd": 1381537193
        },
        "trust_score": "green",
        "bid_ask_spread_percentage": 0.010014,
        "timestamp": "2024-04-07T15:23:02+00:00",
        "last_traded_at": "2024-04-07T15:23:02+00:00",
        "last_fetch_at": "2024-04-07T15:24:00+00:00",
        "is_anomaly": false,
        "is_stale": false,
        "trade_url": "https://www.binance.com/en/trade/BTC_USDT?ref=37754157",
        "token_info_url": null,
        "coin_id": "bitcoin",
        "target_coin_id": "tether"
        }
    ]
    }
    """
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

    return data

    # market_cap = decimal.Decimal(data["market_data"]["market_cap"]["usd"])
    # rank = data["market_cap_rank"]
    # return {
    #     "symbol": data["symbol"],
    #     "market_cap_usd": market_cap,
    #     "market_cap_rank": rank,
    #     "genesis_date": dt.datetime.combine(
    #         dt.date.fromisoformat(data["genesis_date"]), dt.datetime.min.time()
    #     ).isoformat(),
    # }
