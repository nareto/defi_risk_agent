from src.providers.alchemy import get_portfolio as get_alchemy_portfolio

def get_portfolio(wallet):
    alchemy_portfolio = get_alchemy_portfolio(wallet)
    totUsd = sum(t['usd_value'] for t in alchemy_portfolio)
    out = alchemy_portfolio
    for token in out:
        token['portfolio_percentage_usd'] = float(token['usd_value']/totUsd)
    return out