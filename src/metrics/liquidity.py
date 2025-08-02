from decimal import Decimal, getcontext
from src.data_layer.portfolio import get_portfolio
from src.data_layer.tokens import get_token_or_coin_info


getcontext().prec = 28  # high-precision arithmetic


def get_hhi(wallet: str, normalize: bool = False) -> float:
    """
    Herfindahl-Hirschman Index of a wallet’s USD-denominated holdings.
    A higher index signifies higher concentration in few assets.
    Returns 0-10 000 by default; set `normalize=True` for 0-1 scale.
    """
    portfolio = get_portfolio(wallet)
    if not portfolio:
        return 0.0

    usd_values = [p["usd_value"] for p in portfolio if p["usd_value"] > 0]
    total = sum(usd_values)
    if total == 0:
        return 0.0

    hhi = sum(((v / total) * 100) ** 2 for v in usd_values)  # 0–10 000
    return float(hhi / 10_000) if normalize else float(hhi)


   

def get_exotic_exposure(wallet:str, topn_tokens = 200, top_new_days = 90):
    portfolio  = get_portfolio(wallet)
    total_usd  = sum(p["usd_value"] for p in portfolio)
    exotic_usd = 0
    for p in portfolio:
        info = get_token_or_coin_info(p["token_address"])
        if (info['market_cap_rank'] > topn_tokens) or (info['lifetime_seconds'] < top_new_days*24*60*60):
            exotic_usd += p["usd_value"]

    return exotic_usd / total_usd if total_usd else 0.0


