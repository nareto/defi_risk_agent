# defi risk areas and metrics

* * *

### 1. Protocol & Smart Contract Risk

This category assesses the inherent risk of the code and design of the DeFi protocols a wallet interacts with. It focuses on security, reliability, and trustworthiness.

- **Audit Count & Recency:** The number of independent security audits a protocol has undergone and the number of days since the most recent one.
- **Audit Coverage Ratio:** The percentage of a protocol's smart contract lines of code or cyclomatic paths covered in audit reports.
- **Bug-Bounty Ceiling:** The maximum dollar value of the active bug bounty offered by the protocol.
- **Exploit History Score:** The total value (e.g., in USD) lost in a protocol's past exploits or economic attacks, potentially time-weighted to penalize recent events more heavily.
- **Known Exploit Interaction:** A binary flag indicating if the wallet interacted with a protocol *before* a major, publicly known exploit occurred.
- **External Safety Ratings:** Composite scores from third-party rating services like DeFiSafety (PQR), CertiK (Skynet), or CER.
- **Protocol Age Utilization:** The percentage of a wallet's transactions or value deployed in protocols launched within a short timeframe (e.g., less than 90 days).
- **Low-TVL Protocol Concentration:** The percentage of a wallet's assets deployed in protocols with a Total Value Locked (TVL) below a specific threshold (e.g., <$5M).
- **Audit Status Interaction Frequency:** The ratio of interactions with unaudited protocols versus those with one or more public audits.
- **Governance Token Reliance:** The percentage of the wallet's value held in the governance tokens of new or nascent protocols as opposed to established blue-chip ones.

* * *

### 2. Market, Liquidity & Asset Risk

This category covers risks arising from asset price movements, the ability to exit positions without significant loss, and the composition of the assets themselves.

- **Asset Volatility Exposure:** The weighted average of the 30-day realized volatility (`σ₃₀`) of all assets held in the wallet and within its LP positions.
- **Max Drawdown (MDD₉₀):** The worst peak-to-trough price decline for the wallet's held assets over a 90-day period.
- **Impermanent Loss (IL) Sensitivity / VAR:** The estimated potential for impermanent loss based on the volatility and correlation of asset pairs in LP positions, or a formal Value-at-Risk (VaR) calculation for IL.
- **Exotic & Unproven Asset Exposure:** The percentage of wallet value held in assets outside the top 100-200 by market capitalization or in tokens with a very short history.
- **Stablecoin De-Peg Exposure:** The percentage of wallet value held in non-major, experimental, or under-collateralized stablecoins.
- **Portfolio Concentration Index:** The Herfindahl-Hirschman Index (HHI) calculated on the wallet's holdings to measure diversification. A score near 1 indicates high concentration risk.
- **Pool TVL & TVL Volatility (σₜᵥₗ):** The absolute TVL of the liquidity pools used and the standard deviation of that TVL over time.
- **Low-Liquidity Pool Concentration:** The percentage of a wallet's LP value that is in pools with low absolute TVL or a low daily volume-to-TVL ratio.
- **Effective Depth / Price Impact:** The percentage of slippage incurred for a benchmark-sized swap (e.g., swapping 1% of a pool's assets).
- **Pool Net Flow Ratio:** The absolute value of `(inflows – outflows) / TVL` for a given pool over a set period (e.g., 24 hours or 7 days).
- **LP Concentration Index:** The Gini coefficient or HHI of the LP token holder distribution for a specific pool, indicating ownership concentration.
- **Wallet's Share of Pool:** The wallet's own liquidity contribution as a percentage of a pool's total TVL.
- **Asset Correlation to Majors:** The statistical correlation of the wallet's held assets to market benchmarks like Bitcoin (BTC) and Ethereum (ETH).

* * *

### 3. Leverage & Liquidation Risk

This category focuses on the use of borrowed funds and derivatives, which amplify both potential gains and losses, introducing the risk of forced position closure.

- **Loan-to-Value (LTV) / Health Factor:** The wallet's current LTV ratio (`Total Debt / Total Collateral`) or health factor across all lending platforms.
- **Liquidation Distance (Δₗᵢq):** The percentage drop in collateral asset prices that would trigger a liquidation event.
- **Probability of Liquidation (t):** An analytical or model-based probability of the wallet's positions being liquidated over a specific time horizon.
- **Historical Liquidation Events:** The total count of past liquidation events associated with the wallet address.
- **Leveraged Position Activity:** The frequency or total value of transactions indicative of leverage, such as borrowing followed immediately by depositing into a yield farm.
- **Complex Derivative Exposure:** A flag or count of interactions with options, perpetual futures, or other exotic structured products.
- **Liquidation Market Depth vs. Debt:** The ratio of available market liquidity for a collateral asset versus the size of the wallet's debt, indicating how easily the position could be liquidated without causing significant price impact.

* * *

### 4. User Behavior & Strategy Risk

This category quantifies the wallet owner's habits and strategies, directly measuring "degen" activity like chasing high yields and frequent trading.

- **Portfolio Churn Rate:** The value of assets swapped or transferred out of the wallet over a period, calculated as a percentage of the wallet's average total value.
- **Average Position Holding Time (τₕ):** The average duration between acquiring and disposing of DeFi assets, such as LP tokens or staked assets.
- **Protocol Hopping / Pool Switch Frequency:** The number of unique new protocols or liquidity pools the wallet interacts with over a set period (e.g., per month).
- **Average Pool Age at Entry:** The average age of a liquidity pool (since its creation) at the moment the wallet first deposits funds into it.
- **APY Chase Z-Score:** The statistical deviation of the APY of protocols the wallet chooses compared to the median APY available in the market at that time.
- **High-Urgency Gas Spending:** The wallet's average gas price paid relative to the network's average price at the time of its transactions.
- **Interaction Complexity:** A score based on the number of distinct steps in a user's common transaction patterns (e.g., a simple swap vs. a multi-step leverage-farming loop).
- **Wallet Age & Activity Consistency:** The age of the wallet based on its first transaction and the consistency of its investment strategy over time.

* * *

### 5. Systemic & Infrastructure Risk

This category captures broader, external risks inherited from the underlying blockchain, oracles, bridges, governance structures, and the regulatory environment.

#### **Oracle & Data-Feed Risk**

- **Feed Type & Redundancy:** The type of oracle a protocol relies on (e.g., Chainlink, Pyth, TWAP) and its degree of decentralization.
- **Median Update Interval & Staleness:** The typical time between oracle price updates and the number of times the feed has been stale.
- **Circuit Breaker Presence:** A flag indicating if the oracle system has built-in safeguards to halt updates during extreme, anomalous price events.

#### **Governance & Admin-Key Risk**

- **Admin-Key Authority Score:** A score reflecting the power of admin keys (e.g., the ability to pause contracts, upgrade logic, or seize funds).
- **Timelock Delay:** The mandatory time delay (in hours or days) between a governance vote passing and the proposed change being executed.
- **Governance Token Concentration:** The Nakamoto coefficient or HHI for a protocol's governance token distribution, measuring voting power concentration.
- **Emergency Action History:** A count of past instances where protocol administrators used emergency powers to pause or modify the system.

#### **Cross-Chain Bridge & Base-Chain Risk**

- **Bridged Asset Exposure:** The percentage of the wallet's total value held in bridged (non-native) assets.
- **Bridge Hack Risk Index:** A risk score for a specific bridge based on its security history, audit quality, and total value lost in past hacks.
- **Bridge Validator/Multisig Set Size:** The number of signers or validators required to approve transactions on a bridge.
- **Base-Chain Consensus Security:** The Nakamoto coefficient of the underlying L1 or L2 blockchain.
- **Historical Downtime Incidents:** The number of significant outage or performance degradation events on the base chain per year.
- **Base-Chain Gas Fee Volatility:** The standard deviation of transaction priority fees on the network.

#### **Regulatory & Compliance Risk**

- **Sanctioned Counterparty Exposure:** The percentage of transactions or value that has interacted with government-sanctioned addresses (e.g., the OFAC list).
- **Mixer Exposure Score:** The total value or frequency of funds being routed through privacy mixers.
- **Jurisdictional Risk:** The percentage of funds flowing to or from centralized exchanges located in high-risk legal jurisdictions.
- **Protocol Legal Scrutiny:** A flag indicating interaction with protocols that are subject to active, public legal cases or regulatory enforcement actions.

* * *

### 6. Yield Sustainability & Composition Risk

This category evaluates the quality and likely longevity of the yield being earned, distinguishing sustainable, fee-based returns from temporary, inflationary ones.

- **APY Composition:** The percentage of a stated APY that is derived from inflationary token emissions versus real yield from trading fees or other protocol revenue.
- **Emission Half-Life:** The scheduled time until the protocol's block rewards (token emissions) are set to be cut in half.
- **Rewards-to-Float Ratio:** The rate of daily token emissions as a percentage of the total circulating supply, measuring the daily inflationary pressure.
- **Dollar Subsidy per $TVL:** The dollar value of token incentives paid out daily for each dollar of liquidity provided to the protocol.