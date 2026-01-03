from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from tool import country_lookup, get_time_for_timezone, upcoming_public_holidays, fx_rate

import os

os.environ["OPENAI_API_KEY"] = "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"
model = init_chat_model("openai:gpt-4o-mini")

country_agent = create_agent(
    model,
    tools=[country_lookup],
    system_prompt=(
        "You are a country facts agent. "
        "Use the tool to fetch authoritative country details, then summarize clearly."
    ),
)

time_agent = create_agent(
    model,
    tools=[country_lookup, get_time_for_timezone],
    system_prompt=(
        "You are a local-time agent. "
        "If user gives a country name, first call country_lookup to get a timezone. "
        "Pick the most relevant timezone (usually the first) and call get_time_for_timezone. "
        "Return the local time in a concise way."
    ),
)

holidays_agent = create_agent(
    model,
    tools=[country_lookup, upcoming_public_holidays],
    system_prompt=(
        "You are a holidays agent. "
        "If user gives a country name, call country_lookup to get the country code, "
        "then call upcoming_public_holidays(country_code, days_ahead=10). "
        "Summarize the upcoming holidays."
    ),
)

fx_agent = create_agent(
    model,
    tools=[fx_rate],
    system_prompt=(
        "You are an FX agent. "
        "Extract FROM and TO currencies from the user request (prefer ISO like INR, JPY, USD, EUR). "
        "If missing, ask for them in the response. Otherwise call fx_rate(from_ccy, to_ccy) and present it."
    ),
)