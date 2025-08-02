from src.providers.coingecko import (
    get_token_marketcap_and_rank,
    get_coin_marketcap_and_rank,
)
from src.providers.ethplorer import get_token_market_cap_and_creation_date
import datetime as dt

def get_token_or_coin_info(address, network ='ethereum'):
    if address is None:
        return get_coin_info(network)
    else:
        return get_token_info(address)

def get_token_info(address):
    cg_token_data = get_token_marketcap_and_rank(address)
    ep_token_data = get_token_market_cap_and_creation_date(address)
    lifetime = (
        dt.datetime.now()
        - dt.datetime.fromisoformat(ep_token_data["creation_date_isoformat"])
    ).total_seconds()
    token_data = dict(
        cg_token_data,
        lifetime_seconds=lifetime,
        **ep_token_data,
    )  # ep_token favoured for duplicates

    return token_data


def get_coin_info(network):
    cg_coin = get_coin_marketcap_and_rank(network)
    return {
        "symbol": cg_coin["symbol"],
        "market_cap_usd": cg_coin["market_cap_usd"],
        "market_cap_rank": cg_coin["market_cap_rank"],
        "lifetime_seconds": (
            dt.datetime.now() - dt.datetime.fromisoformat(cg_coin["genesis_date"])
        ).total_seconds(),
    }
