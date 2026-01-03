```mermaid
flowchart TD
    U[User Query<br/>Travel to Japan next week...] --> R[Router LLM<br/>Structured Output]

    R -->|route: country| C[Country Agent<br/>LLM + Tools]
    R -->|route: time| T[Time Agent<br/>LLM + Tools]
    R -->|route: holidays| H[Holidays Agent<br/>LLM + Tools]
    R -->|route: fx| F[FX Agent<br/>LLM + Tools]

    %% Country Agent internals
    C --> CT[Tool: country_lookup<br/>REST Countries API]

    %% Time Agent internals
    T --> T1[Tool: country_lookup]
    T1 --> T2[Tool: get_time_for_timezone<br/>WorldTimeAPI]

    %% Holidays Agent internals
    H --> H1[Tool: country_lookup]
    H1 --> H2[Tool: upcoming_public_holidays<br/>Nager.Date API]

    %% FX Agent internals
    F --> FX[Tool: fx_rate<br/>Frankfurter API]

    %% Fan-in
    CT --> AGG[(Results Reducer)]
    T2 --> AGG
    H2 --> AGG
    FX --> AGG

    %% Final synthesis
    AGG --> S[Synthesizer LLM]
    S --> A[Final Answer]
    ```