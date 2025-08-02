# Architecture

providers -> data_layer -> metrics

providers: simple wrapper functions around specific third-party API's endpoints
data_layer: is an abstraction layer on top of providers, doing necessary aggregation and transformations to get the data we need
metrics: the complex metrics computed from data_layer


```mermaid
flowchart TD
    %% ─── Nodes ──────────────────────────────
    Start([Start])
    Agent[[LLM<br/>agent&nbsp;node]]
    Action{{Execute<br/>tool&nbsp;calls}}
    Summarize[/Summarize&nbsp;metrics&nbsp;–&nbsp;risk&nbsp;JSON/]
    End([End])

    %% ─── Edges ──────────────────────────────
    Start --> Agent
    Agent -->|all&nbsp;metrics&nbsp;ready| Summarize
    Agent -->|needs&nbsp;tool&nbsp;calls| Action
    Agent -->|no&nbsp;tool&nbsp;calls&nbsp;and<br/>still&nbsp;missing&nbsp;metrics| End
    Action --> Agent
    Summarize --> End

    %% ─── Styles (colorful!) ─────────────────
    classDef start   fill:#A6E1FA,stroke:#0077B6,stroke-width:2px,color:#003049;
    classDef llm     fill:#97F0AA,stroke:#2A7F62,stroke-width:2px,color:#003824;
    classDef tool    fill:#FFE17C,stroke:#BB8600,stroke-width:2px,color:#664400;
    classDef summary fill:#FFA5B5,stroke:#C2185B,stroke-width:2px,color:#73002C;
    classDef finish  fill:#D4C0FA,stroke:#5B21B6,stroke-width:2px,color:#2B0A3D;

    class Start start
    class Agent llm
    class Action tool
    class Summarize summary
    class End finish

```