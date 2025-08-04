# Defi Risk Agent
![alt text](image.png)

This is a PoC [LangGraph](https://www.langchain.com/langgraph) AI agent that takes an Ethereum wallet in input and, by looking at what DeFi activity they are involved with, produces a 0-100 score representing the tolerance for risk of the investor. 


# ✨ Features
- 🖥️  Dual interface: Next.js frontend and CLI
- 🛠️  **Modular plug-in architecture** – adding new `api_*` or `metric_*` tools is simple (see [Agent Architecture](#agent-architecture))
- 📊 **Structured output** – final assessment is strict JSON that your code can rely on (powered by [instructor](https://github.com/567-labs/instructor))
- 📝 **Checkpoint & replay** – every run is snap-shotted to Postgres/sqlite; resume any thread/turn with `just resume <thread_id>:<turn>` (Note: this will re-execute API calls)
- 🚦 **Per-provider rate-limits** – set API limits with `@rate_limit` decorator
- ⛔ Hard cap of `--max-turns` LLM calls (default 10) to keep costs predictable
- 📨 Sends only the last `--max-messages` (default 7) back to the model each turn – keeps context tight and cheap
- 📑 Optional JSON log output with `--log-format json` for seamless ingestion in observability stacks

_This IS a proof-of-concept, and the generated risk score is not reliable_

# Quickstart
To run commands in the [justfile](justfile) shown here, you need  [just](https://github.com/casey/just)

## Frontend
Run

```
just dc up --build -d
```


## CLI

Install with [poetry](https://python-poetry.org/docs/):

```
poetry install
```

Run manually for one address :

```
just run 0x7a29aE65Bf25Dfb6e554BF0468a6c23ed99a8DC2
```

or without using just:

```
poetry run -m src.cli 0x7a29aE65Bf25Dfb6e554BF0468a6c23ed99a8DC2
```


For a batch of addresses:

```
just brun
```

or

```
./batch_run.sh
```

# Agent Architecture

The architecture consists of a main `LLM->tools->LLM` loop. The LLM calls `api_*` tools (in [src/providers](src/providers)) to gather data, then uses this to compute `metric_*` tools (in [src/metrics](src/metrics)) which provide risk metrics - see [Risk Metrics](#risk-metrics). The main prompt used at each iteration can be found [here](src/prompts/system.md). Finally, all the computed metrics are passed to a final prompt, (available [here](src/prompts/risk.md)) that asks the LLM to make a subjective assessment of the risk, based on the provided metrics.


```mermaid
flowchart TB
    %% edges first to influence layout
    setup --> agent
    agent -->|tool choice| action
    agent -->|computed metrics| finalize
    action --> |tool output| memory
    memory --> agent

    memory[(stack AI+tool messages)]

    %% standalone nodes (implicitly created by edges)
    setup[[setup]]
    agent{LLM collects data}
    finalize[LLM assigns risk score]

    %% subgraph for tools
    subgraph action["tools"]
        direction LR
        apiTools[api_*]
        metricTools[metric_*]
        utilTools[util_*]
    end

```


## Motivation
The core insight that drove this design is that we can think of metrics as pure functions, where we can easily use the typing system to specify very precisely the required inputs and expected outputs, whereas api calls can be considered as messy JSON blobs, with each data provider choosing their own format. Sure, we could painstakingly map them out, and maintain our data types to stay up-to-date with upstream schema changes... but why not use LLMs for that? The main loop is basically doing just that, asking the LLM to figure out what data it needs to compute the metrics, then query api endpoints that sound promising, extract what it needs, until finally it can compute the metrics.

## Extending toolset
The implementation of both `api_*` wrapper functions and `metrics_*` tools is completely decoupled from the rest of the code. This makes adding more data sources and output metrics very easy.


## Risk Metrics
With the help of AI I came up with an extensive list of metrics that can be used to measure risk, see [defi_risk_metrics.md](defi_risk_metrics.md) for a full list, divided by macro-area. Out of these I selected the following, which are currently implemented in [src/metrics](src/metrics/):

1. Portfolio Concentration Index (HHI): calculated on the wallet's holdings to measure diversification. A score near 1 signifies high concentration in a single asset.
2. Exotic & Unproven Asset Exposure: the percentage of a wallet's value held in assets that are outside the top 100–200 by market capitalization or have a very short history.
3. Low-TVL Protocol Concentration: the percentage of a wallet's assets that are deployed in protocols with a Total Value Locked (TVL) below a certain threshold, such as $5 million.
4. Portfolio Churn Rate: the value of assets swapped or transferred out over a period, calculated as a percentage of the wallet's average total value.
5. Bridged Asset Exposure: the percentage of the wallet's total value that is held in bridged (non-native) assets.
