from src.providers.coingecko import (
    api_coingecko_contract,
    api_coingecko_coin_data,
)
from src.providers.ethplorer import api_ethplorer_token_data
from src.providers.dexscreener import get_token_info
import datetime as dt

def get_token_or_coin_info(address, network ='ethereum'):
    if address is None:
        return get_coin_info(network)
    else:
        return get_token_info(address)

def get_token_info(address):
    token_info_providers = {
        'coingecko': api_coingecko_contract,
        'ethplorer': api_ethplorer_token_data,
        'dexscreener': get_token_info
    }

    cg_token_data = api_coingecko_contract(address)
    ep_token_data = api_ethplorer_token_data(address)
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
    cg_coin = api_coingecko_coin_data(network)
    return {
        "symbol": cg_coin["symbol"],
        "market_cap_usd": cg_coin["market_cap_usd"],
        "market_cap_rank": cg_coin["market_cap_rank"],
        "lifetime_seconds": (
            dt.datetime.now() - dt.datetime.fromisoformat(cg_coin["genesis_date"])
        ).total_seconds(),
    }
