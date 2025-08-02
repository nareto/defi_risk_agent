import os
import pprint

import requests
from langchain_core.tools import tool
from src.utils import rate_limit
from typing import Annotated  


BASE   = "https://deep-index.moralis.io/api/v2.2"
HEAD   = {"X-API-Key": os.getenv("MORALIS_API_KEY")}

@tool
@rate_limit(max_calls=2, period_seconds=10)
def api_moralis_wallet_portfolio(address: str, chain: str = "eth", limit: int = 500):
    """Return ERC-20 token balances (USD prices included)."""
    url    = f"{BASE}/{address}/erc20"
    params = {"chain": chain, "limit": limit}
    r = requests.get(url, headers=HEAD, params=params, timeout=30)
    r.raise_for_status()
    return r.json()        # → list[dict]
    # {'token_address': '0x1596f7f7a0c495daf141376321d3ecac66a10a42',
    # 'symbol': 'SORA',
    # 'name': 'Sora',
    # 'logo': None,
    # 'thumbnail': None,
    # 'decimals': 18,
    # 'balance': '15382104000000000000000',
    # 'possible_spam': True,
    # 'verified_contract': False,
    # 'total_supply': '600000000000000000000000000',
    # 'total_supply_formatted': '600000000',
    # 'percentage_relative_to_total_supply': 0.002563684,
    # 'security_score': None}

@tool
@rate_limit(max_calls=2, period_seconds=10)
def api_moralis_wallet_history(address: str, chain: str = "eth",
                       cursor: str | None = None, page_size: int = 100):
    """
    Return one page of decoded wallet history.
    Re-feed the returned cursor to paginate.
    """
    url    = f"{BASE}/wallets/{address}/history"
    params = {"chain": chain, "page_size": page_size}
    if cursor:
        params["cursor"] = cursor
    r = requests.get(url, headers=HEAD, params=params, timeout=30)
    r.raise_for_status()
    return r.json()        # keys: result[], cursor, page
    # {
    #   "page": "2",
    #   "page_size": "100",
    #   "cursor": "",
    #   "result": [
    #     {
    #       "hash": "0x1ed85b3757a6d31d01a4d6677fc52fd3911d649a0af21fe5ca3f886b153773ed",
    #       "nonce": "1848059",
    #       "transaction_index": "108",
    #       "from_address_entity": "Opensea",
    #       "from_address_entity_logo": "https://opensea.io/favicon.ico",
    #       "from_address": "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0",
    #       "from_address_label": "Binance 1",
    #       "to_address_entity": "Beaver Build",
    #       "to_address_entity_logo": "https://beaverbuild.com/favicon.ico",
    #       "to_address": "0x003dde3494f30d861d063232c6a8c04394b686ff",
    #       "to_address_label": "Binance 2",
    #       "value": "115580000000000000",
    #       "gas": "30000",
    #       "gas_price": "52500000000",
    #       "receipt_cumulative_gas_used": "4923073",
    #       "receipt_gas_used": "21000",
    #       "receipt_contract_address": "",
    #       "receipt_root": "",
    #       "receipt_status": "1",
    #       "block_timestamp": "2021-05-07T11:08:35.000Z",
    #       "block_number": "12386788",
    #       "block_hash": "0x9b559aef7ea858608c2e554246fe4a24287e7aeeb976848df2b9a2531f4b9171",
    #       "internal_transactions": [
    #         {
    #           "transaction_hash": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "block_number": "12526958",
    #           "block_hash": "0x0372c302e3c52e8f2e15d155e2c545e6d802e479236564af052759253b20fd86",
    #           "type": "CALL",
    #           "from": "0xd4a3BebD824189481FC45363602b83C9c7e9cbDf",
    #           "to": "0xa71db868318f0a0bae9411347cd4a6fa23d8d4ef",
    #           "value": "650000000000000000",
    #           "gas": "6721975",
    #           "gas_used": "6721975",
    #           "input": "0x",
    #           "output": "0x"
    #         }
    #       ],
    #       "nft_transfers": [
    #         {
    #           "token_address": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "token_id": "15",
    #           "from_address_entity": "Opensea",
    #           "from_address_entity_logo": "https://opensea.io/favicon.ico",
    #           "from_address": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "from_address_label": "Binance 1",
    #           "to_address_entity": "Beaver Build",
    #           "to_address_entity_logo": "https://beaverbuild.com/favicon.ico",
    #           "to_address": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "to_address_label": "Binance 2",
    #           "value": "1000000000000000",
    #           "amount": "1",
    #           "contract_type": "ERC721",
    #           "block_number": "88256",
    #           "block_timestamp": "2021-06-04T16:00:15",
    #           "block_hash": "string",
    #           "transaction_hash": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "transaction_type": "string",
    #           "transaction_index": 1,
    #           "log_index": 1,
    #           "operator": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "possible_spam": "",
    #           "verified_collection": ""
    #         }
    #       ],
    #       "erc20_transfer": [
    #         {
    #           "token_name": "Tether USD",
    #           "token_symbol": "USDT",
    #           "token_logo": "https://assets.coingecko.com/coins/images/325/large/Tether-logo.png?1598003707",
    #           "token_decimals": "6",
    #           "transaction_hash": "0x2d30ca6f024dbc1307ac8a1a44ca27de6f797ec22ef20627a1307243b0ab7d09",
    #           "address": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "block_timestamp": "2021-04-02T10:07:54.000Z",
    #           "block_number": "12526958",
    #           "block_hash": "0x0372c302e3c52e8f2e15d155e2c545e6d802e479236564af052759253b20fd86",
    #           "to_address_entity": "Beaver Build",
    #           "to_address_entity_logo": "https://beaverbuild.com/favicon.ico",
    #           "to_address": "0x62AED87d21Ad0F3cdE4D147Fdcc9245401Af0044",
    #           "to_address_label": "Binance 2",
    #           "from_address_entity": "Opensea",
    #           "from_address_entity_logo": "https://opensea.io/favicon.ico",
    #           "from_address": "0xd4a3BebD824189481FC45363602b83C9c7e9cbDf",
    #           "from_address_label": "Binance 1",
    #           "value": "650000000000000000",
    #           "transaction_index": 12,
    #           "log_index": 2,
    #           "possible_spam": "",
    #           "verified_contract": ""
    #         }
    #       ],
    #       "native_transfers": [
    #         {
    #           "from_address_entity": "Opensea",
    #           "from_address_entity_logo": "https://opensea.io/favicon.ico",
    #           "from_address": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "from_address_label": "Binance 1",
    #           "to_address_entity": "Beaver Build",
    #           "to_address_entity_logo": "https://beaverbuild.com/favicon.ico",
    #           "to_address": "0x057Ec652A4F150f7FF94f089A38008f49a0DF88e",
    #           "to_address_label": "Binance 2",
    #           "value": "1000000000000000",
    #           "value_formatted": "0.1",
    #           "direction": "outgoing",
    #           "internal_transaction": "",
    #           "token_symbol": "ETH",
    #           "token_logo": "https://cdn.moralis.io/eth/0x67b6d479c7bb412c54e03dca8e1bc6740ce6b99c.png"
    #         }
    #       ]
    #     }
    #   ]
    # }
