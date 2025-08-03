# Defi Risk Agent
This is a PoC AI agent that takes an Ethereum wallet in input and, by looking at what DeFi activity they are involved with, produces a 0-100 score representing the tolerance for risk of the investor. 

# Features
- 
- resume from a previous run from a specific turn with `just resume threadid:turn`
- hard stop at `--max-turns` LLM invocations (default: 10)
- pass only the last `--max-messages` to each LLM invocation (default: 7)
- json logs with `--log-format json`

# Installation
`poetry install`

# Running
Manually for one address:

`just run 0x7a29aE65Bf25Dfb6e554BF0468a6c23ed99a8DC2`

or, if you don't have [just](0x7a29aE65Bf25Dfb6e554BF0468a6c23ed99a8DC2):

`poetry run -m src.cli 0x7a29aE65Bf25Dfb6e554BF0468a6c23ed99a8DC2`


For a batch of addresses:

`just brun`

or

`./batch_run.sh`

# Architecture
