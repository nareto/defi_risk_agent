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


def get_exotic_exposure(wallet: str) -> float:
    """
    Exotic exposure risk, based on portfolio allocation to low cap or short-lived tokens
    """
    portfolio = get_portfolio(wallet)
    exposure = 0
    for token_portfolio in portfolio:
        token_address = token_portfolio['token_address']
        token_info = get_token_or_coin_info(token_address)
        exposure += token_portfolio['portfolio_percentage_usd']*token_info['market_cap_rank']/token_info['lifetime_seconds']
    return exposure
    

