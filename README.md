# TODO
## data

**1. Portfolio Concentration Index (HHI)**

* **What it is:** The Herfindahl-Hirschman Index (HHI) is calculated on the wallet's holdings to measure diversification. A score near 1 signifies high concentration in a single asset.
* **Why it's a good choice:** This is a classic, powerful financial metric that is straightforward to calculate. It immediately flags wallets that are over-exposed to the price movement of a single asset, which is a fundamental risk.
* **Implementation Feasibility:** High. You can get a wallet's token holdings and their USD values from a portfolio API (like Zapper, Zerion, or Covalent). The HHI calculation is simple mathematics on that data.

**2. Exotic & Unproven Asset Exposure**

* **What it is:** The percentage of a wallet's value held in assets that are outside the top 100–200 by market capitalization or have a very short history.
* **Why it's a good choice:** This is an excellent and easy-to-implement proxy for asset quality risk. It quickly identifies wallets holding speculative memecoins or other high-volatility assets, which are inherently riskier than established blue-chip assets.
* **Implementation Feasibility:** High. You can use the CoinGecko API to get a list of the top 200 tokens by market cap. Compare the wallet's holdings (from a portfolio API) against this list to calculate the percentage.

**3. Low-TVL Protocol Concentration**

* **What it is:** The percentage of a wallet's assets that are deployed in protocols with a Total Value Locked (TVL) below a certain threshold, such as \$5 million.
* **Why it's a good choice:** TVL is a widely accepted proxy for a protocol's trust, liquidity, and security (the “Lindy” effect). Interacting with low-TVL protocols is a significant risk factor, as they are often newer, unaudited, and have higher chances of failure or exploit.
* **Implementation Feasibility:** Medium-High. The DeFiLlama API provides TVL data for thousands of protocols. You would need to get the wallet's active positions (e.g., LP tokens in a specific pool) from a portfolio API and then cross-reference the protocol's TVL via DeFiLlama.

**4. Portfolio Churn Rate**

* **What it is:** The value of assets swapped or transferred out over a period, calculated as a percentage of the wallet's average total value.
* **Why it's a good choice:** This is a fantastic metric for quantifying user behavior risk. A high churn rate indicates frequent trading, aping into new trends, or chasing yields — all strategies that carry higher risk than a long-term holding strategy. This directly addresses the quantification of "degen" activity.
* **Implementation Feasibility:** Medium. You need to fetch the wallet's transaction history for a period (e.g., 30 days) from an API like Covalent or Etherscan. Sum the value of swaps/transfers and divide by the wallet's average balance over that period.

**5. Bridged Asset Exposure**

* **What it is:** The percentage of the wallet's total value that is held in bridged (non-native) assets.
* **Why it's a good choice:** This metric addresses systemic and infrastructure risk. Bridges are one of the most frequently hacked pieces of crypto infrastructure. Holding a large percentage of assets in a wrapped/bridged form exposes the user to the risk of that specific bridge failing, in addition to the risk of the asset itself. It shows a more nuanced understanding of Web3 risk.
* **Implementation Feasibility:** Medium. You can identify bridged assets by their contract addresses or tickers (e.g., WETH, USDC.e). Use a portfolio API to get wallet holdings and identify which assets are non-native to the analyzed chain.

## agent