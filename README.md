# Travel Concierge – Router Pattern with Free APIs

## Overview

Travel Concierge is a multi-agent router-style application built using LangChain and a graph-based workflow.  
It demonstrates how a single user query can be decomposed and routed to specialized agents that fetch live, authoritative data from free public APIs.

The project intentionally avoids paid services, authentication-heavy APIs, and regex-based sanitization.  
All data dependencies are handled through deterministic tools wherever possible.

## Example User Query

"I'm traveling to Japan next week. What time is it there right now, are there any upcoming public holidays, what's the current exchange rate from INR to JPY, and can you share some basic facts about Japan?"

## What the System Answers

- Current local time at the destination
- Upcoming public holidays in the destination country
- Live foreign exchange rate
- Basic country facts

All results are combined into a single coherent response.

---

## Architecture Summary

The system follows a **router pattern**:

1. The user submits a single query.
2. A router classifies which information is required.
3. Specialized agents are invoked.
4. Each agent uses one or more tools.
5. Results are aggregated into a final response.

The LLM is used for:
- Routing
- Tool selection
- Final synthesis

The LLM is **not** trusted for real-time data.

---

## Project Structure
## Project Structure

```text
├── tools.py      # All external API tools
├── agents.py     # Sub-agents built on top of tools
├── routing.py    # Routing logic
├── workflow.py   # Graph/workflow orchestration
├── main.py       # CLI entry point
└── README.md
```

---

## Tools and Data Sources

This section describes **each tool**, its **data source**, and **why it exists**.

### 1. Country Lookup Tool

**Tool Name**
- `country_lookup(country_name: str) -> dict`

**API Used**
- Rest Countries API  
  https://restcountries.com

**Purpose**
- Fetch authoritative country metadata.
- Provide capital city coordinates required for downstream time calculation.

**Returned Data**
- Country name
- Capital
- ISO country code
- Timezones
- Currencies
- Capital latitude
- Capital longitude

This tool returns a **dictionary**, not text, because other tools depend on its output.

---

### 2. Local Time from Coordinates Tool

**Tool Name**
- `local_time_from_latlon(latitude: float, longitude: float) -> dict`

**API Used**
- Open-Meteo API  
  https://open-meteo.com

**Purpose**
- Determine the correct IANA timezone.
- Fetch the current local time reliably.

**Returned Data**
- Timezone (IANA format)
- Local datetime

This avoids flaky world-time APIs and avoids timezone guessing.

---

### 3. Upcoming Public Holidays Tool

**Tool Name**
- `upcoming_public_holidays(country_code: str, days_ahead: int = 10) -> str`

**API Used**
- Nager.Date API  
  https://date.nager.at

**Purpose**
- Retrieve upcoming public holidays for the destination country.

**Returned Data**
- A formatted list of holidays within the specified window.

---

### 4. Foreign Exchange Rate Tool

**Tool Name**
- `fx_rate(from_ccy: str, to_ccy: str) -> str`

**API Used**
- Frankfurter API  
  https://www.frankfurter.app

**Purpose**
- Retrieve live FX rates without authentication.

**Returned Data**
- Exchange rate with date context.

---

## Agents

### Country Facts Agent
- Uses `country_lookup`
- Summarizes country information

### Time Agent
- Uses a tool-forced model (`tool_choice="required"`)
- Always calls:
  1. `country_lookup`
  2. `local_time_from_latlon`
- Never answers from model knowledge

### Holidays Agent
- Uses:
  - `country_lookup`
  - `upcoming_public_holidays`

### FX Agent
- Uses:
  - `fx_rate`

---

## Tool Enforcement (Important)

The Time Agent binds tools using:

```
tool_choice="required"
```


This ensures:
- The model **cannot** answer from general knowledge
- Real-time data is always fetched from APIs
- No hallucinated timestamps or UTC offsets

---

## Mermaid Flow Diagram

```mermaid
flowchart TD
    A[User Query] --> B[Router]

    B --> C1[Time Agent]
    B --> C2[Holidays Agent]
    B --> C3[FX Agent]
    B --> C4[Country Facts Agent]

    C1 --> T1[country_lookup]
    T1 --> T2[local_time_from_latlon]
    T2 --> R1[Time Result]

    C2 --> H1[country_lookup]
    H1 --> H2[upcoming_public_holidays]
    H2 --> R2[Holiday Result]

    C3 --> F1[fx_rate]
    F1 --> R3[FX Result]

    C4 --> K1[country_lookup]
    K1 --> R4[Country Facts Result]

    R1 --> Z[Final Aggregation]
    R2 --> Z
    R3 --> Z
    R4 --> Z

    Z --> O[Final Answer]



