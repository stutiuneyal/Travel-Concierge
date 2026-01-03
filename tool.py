from langchain.tools import tool
import requests
import datetime as dt
import time
import random


UA = "TripConciergeRouter/1.0 (demo; contact: you@example.com)"

def _get(url: str, params: dict | None = None, timeout: int = 20, retries: int = 3) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                params=params or {},
                timeout=timeout,
                headers={"User-Agent": UA},
            )
            r.raise_for_status()
            return r.json()

        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            last_err = e
            # exponential backoff + jitter
            sleep_s = (2 ** attempt) + random.random()
            time.sleep(sleep_s)

    # After retries, raise a clean error (or return empty)
    raise RuntimeError(f"HTTP failed after {retries} retries for {url}: {last_err}")


@tool
def country_lookup(country_name: str) -> str:
    """
    Docstring for country_lookup
    
    :param country_name: Description
    :type country_name: str
    :return: Description
    :rtype: str
    """
    data = _get(
       f"https://restcountries.com/v3.1/name/{country_name}",
       params={
           "fullText" : "true"
       }
    )

    if not isinstance(data,list) or not data :
        return f"no country found {country_name}"


    c = data[0]
    name = (c.get("name") or {}).get("common")
    capital = (c.get("capital") or ["na"])[0]
    code = c.get("cca2") or "na"
    timezones= c.get("timezones") or []
    currencies = [] 
    for k,v in (c.get("currencies") or {}).items():
        currencies.append(f"{k} ({v.get('name', '')})") 

    return (
        f"Country: {name}\n"
        f"Capital: {capital}\n"
        f"Code: {code}\n"
        f"Timezones: {', '.join(timezones) if timezones else 'N/A'}\n"
        f"Currencies: {', '.join(currencies) if currencies else 'N/A'}"
    )

@tool
def get_time_for_timezone(timezone: str)-> str:
    """
    Docstring for get_time_for_timezone
    
    :param timezone: Description
    :type timezone: str
    :return: Description
    :rtype: str
    """

    data = _get(
        f"http://worldtimeapi.org/api/{timezone}"
    )

    return (
        f"Timezone: {data.get('timezone')}\n"
        f"Local datetime: {data.get('datetime')}\n"
        f"UTC offset: {data.get('utc_offset')}"
    )

@tool
def upcoming_public_holidays(country_code: str, days_ahead: int=10 ) -> str:
    """
    Docstring for upcoming_public_holidays
    
    :param country_code: Description
    :type country_code: str
    :param days_ahead: Description
    :type days_ahead: int
    :return: Description
    :rtype: str
    """
    today=dt.date.today()
    end = today+dt.timedelta(days=days_ahead)
    years = {today.year, end.year}
    holidays = []
    for y in sorted(years) :
        data = _get(f"https://date.nager.at/api/v3/PublicHolidays/{y}/{country_code}")
        if isinstance(data, list):
            holidays.extend(data) #to add an entire list, append to add only 1 element

    upcoming = []

    for h in holidays:
        d = h.get("date")
        if not d :
            continue
        try:
            hd = dt.date.fromisoformat(d)

        except:
            continue

        if today<=hd<=end:
            upcoming.append(f"{d}: {h.get('name') or ''}")


    if not upcoming:
        return f"No public holidays found between {today} and {end} for {country_code}."

    return "Upcoming public holidays:\n" + "\n".join(sorted(upcoming))


@tool
def fx_rate(from_ccy: str, to_ccy= str) -> str:
    """
    Docstring for fx_rate
    
    :param from_ccy: Description
    :type from_ccy: str
    :param to_ccy: Description
    :return: Description
    :rtype: str
    """

    data = _get("https://api.frankfurter.dev/latest",
                params= {
                    "from" : from_ccy,
                    "to" : to_ccy,
                })
    
    rate = (data.get("rates") or {}).get(to_ccy)

    return f"FX rate on {data.get('date')}: 1 {from_ccy} = {rate} {to_ccy}"
