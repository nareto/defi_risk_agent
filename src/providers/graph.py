import requests
from langchain_core.tools import tool
from src.utils import rate_limit
from typing import Annotated

# ───────────────────────────────────────────────────────────────
# Sub-graph endpoints (add more if needed)
# ───────────────────────────────────────────────────────────────
AAVE_V3_ETH = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3"
AAVE_V2_ETH = "https://api.thegraph.com/subgraphs/name/aave/protocol"

# ───────────────────────────────────────────────────────────────
# 1. Current account data  (collateral, debt, liq-threshold)
# ───────────────────────────────────────────────────────────────
_ACCOUNT_QUERY = """
query ($user: ID!) {
  user(id: $user) {
    id
    totalCollateralUSD
    totalBorrowsUSD               # v2 naming
    totalDebtUSD                  # v3 naming
    currentLiquidationThreshold   # weighted, 0-10000 (bps)
  }
}
"""

@tool
@rate_limit(max_calls=4, period_seconds=10)
def api_graph_aave_account_summary(
    wallet_address: str,
    version: Annotated[str, "v2 or v3"] = "v3",
    chain: Annotated[str, "currently only 'eth' is supported"] = "eth",
) -> dict:
    """
    Fetch aggregated collateral / debt in USD and the weighted liquidation-threshold for a wallet
    from the Aave sub-graph. Field names are normalised for convenience:

    Returns
    -------
    {
      "totalCollateralUSD": float,
      "totalDebtUSD": float,
      "liquidationThreshold": float   # expressed 0-1 (e.g. 0.825)
    }
    """
    if chain != "eth":
        raise NotImplementedError("Only Ethereum main-net sub-graphs bundled for now.")

    url = AAVE_V3_ETH if version == "v3" else AAVE_V2_ETH
    variables = {"user": wallet_address.lower()}
    r = requests.post(url, json={"query": _ACCOUNT_QUERY, "variables": variables}, timeout=30)
    r.raise_for_status()
    data = r.json()["data"]["user"]
    if not data:
        return {
            "totalCollateralUSD": 0.0,
            "totalDebtUSD": 0.0,
            "liquidationThreshold": 0.0,
        }

    collateral = float(data["totalCollateralUSD"])
    # field differs v2/v3
    debt       = float(data.get("totalDebtUSD") or data.get("totalBorrowsUSD") or 0)
    lt_raw     = float(data["currentLiquidationThreshold"])  # 0-10000
    lt         = lt_raw / 10_000.0

    return {
        "totalCollateralUSD": collateral,
        "totalDebtUSD": debt,
        "liquidationThreshold": lt,
    }

# ───────────────────────────────────────────────────────────────
# 2. Historical liquidation events
# ───────────────────────────────────────────────────────────────
_LIQUIDATION_QUERY = """
query ($user: Bytes!, $skip: Int!) {
  liquidations(
    where: { user: $user }
    first: 1000
    skip: $skip
    orderBy: timestamp
    orderDirection: asc
  ) {
    id
    timestamp
  }
}
"""

@tool
@rate_limit(max_calls=4, period_seconds=10)
def api_graph_aave_liquidations(
    wallet_address: str,
    version: Annotated[str, "v2 or v3"] = "v3",
    chain: Annotated[str, "currently only 'eth' is supported"] = "eth",
    max_pages: int = 5,
) -> list[dict]:
    """
    Return *all* liquidation events for a wallet.

    Each page fetches up to 1 000 events; increase `max_pages`
    to enumerate further if required.
    """
    if chain != "eth":
        raise NotImplementedError("Only Ethereum main-net sub-graphs bundled for now.")

    url = AAVE_V3_ETH if version == "v3" else AAVE_V2_ETH
    results: list[dict] = []
    skip = 0
    for _ in range(max_pages):
        variables = {"user": wallet_address.lower(), "skip": skip}
        r = requests.post(url, json={"query": _LIQUIDATION_QUERY, "variables": variables}, timeout=30)
        r.raise_for_status()
        batch = r.json()["data"]["liquidations"]
        if not batch:
            break
        results.extend(batch)
        skip += 1000     # next page
    return results      # [{'id': ..., 'timestamp': ...}, ...]