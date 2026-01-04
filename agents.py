from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from tool import country_lookup, local_time_from_latlon, upcoming_public_holidays, fx_rate

import os

assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY not set"
model = init_chat_model("openai:gpt-4o-mini")

country_agent = create_agent(
    model,
    tools=[country_lookup],
    system_prompt=(
        "You are a country facts agent. "
        "Use the tool to fetch authoritative country details, then summarize clearly."
    ),
)

"""
Agent is still allowed to answer from its own knowledge when it thinks it can, 
and LangChain does not guarantee tool usage unless you hard-enforce it.

Hence we get output like:

### Current Time in Japan
Japan operates on Japan Standard Time (UTC+09:00). If you are traveling next week, please check the current time using a world clock, as I cannot provide real-time information.

"""

tool_model = model.bind_tools(
    tools=[country_lookup, local_time_from_latlon],
    tool_choice="required",
)

time_agent = create_agent(
    tool_model,
    tools=[country_lookup, local_time_from_latlon],
    system_prompt=(
        "You are the Time Agent.\n"
        "You MUST use tools.\n\n"
        "Steps:\n"
        "1) Call country_lookup(country_name).\n"
        "2) Use capital_latitude and capital_longitude.\n"
        "3) Call local_time_from_latlon(latitude, longitude).\n"
        "Return EXACTLY the dict from step 3 (no extra keys, no extra text).\n"
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