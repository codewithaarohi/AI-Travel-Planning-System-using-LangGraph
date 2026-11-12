
# Example free API usage
# - AviationStack


# create api key
# https://aviationstack.com/
# pip install requests



import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

# The AviationStack free plan only allows plain HTTP.
AVIATIONSTACK_URL = "http://api.aviationstack.com/v1/flights"
DATA_NOTE = "AviationStack real-time status data, not fares or bookings"


def _iata(code):
    """Normalise to a 3-letter IATA airport code, or None if it isn't one."""
    code = (code or "").strip().upper()
    return code if re.fullmatch(r"[A-Z]{3}", code) else None


def _fetch(params):
    """Return (rows, error_message). Never includes the API key in the error."""
    try:
        response = requests.get(
            AVIATIONSTACK_URL,
            params={"access_key": API_KEY, "limit": 100, **params},
            timeout=20,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        # The exception text can contain the request URL (with access_key), so only the type is shown.
        return [], f"Flight search failed: could not reach AviationStack ({type(exc).__name__})."

    if "error" in data:
        err = data["error"] or {}
        return [], f"Flight search failed: AviationStack error {err.get('code')}: {err.get('message')}"
    return data.get("data") or [], None


def _format(rows, max_results):
    """One line per operating flight; codeshare listings are collapsed into the flight that operates them."""
    lines, seen = [], set()
    for row in rows:
        flight = row.get("flight") or {}
        codeshare = flight.get("codeshared")
        if codeshare:
            number = (codeshare.get("flight_iata") or "").upper()
            airline = (codeshare.get("airline_name") or "Unknown").title()
        else:
            number = (flight.get("iata") or "").upper()
            airline = (row.get("airline") or {}).get("name") or "Unknown"
        if not number or number in seen:
            continue
        seen.add(number)

        dep = row.get("departure") or {}
        arr = row.get("arrival") or {}
        # AviationStack reports airport-local times (despite the +00:00 suffix).
        departs = (dep.get("scheduled") or "")[:16].replace("T", " ") or "unknown time"
        lines.append(
            f"- {number} {airline}: {dep.get('airport', 'Unknown')} ({dep.get('iata', '?')}) → "
            f"{arr.get('airport', 'Unknown')} ({arr.get('iata', '?')}), departs {departs} local, "
            f"status: {row.get('flight_status', 'unknown')}"
        )
        if len(lines) == max_results:
            break
    return lines


def search_flights(origin_iata=None, destination_iata=None, max_results=5):
    """Search today's live flights into the destination airport, from the origin if one is given."""
    origin, destination = _iata(origin_iata), _iata(destination_iata)
    if not destination:
        return "Flight search skipped: could not identify a destination airport in the request."

    header = f"Live flights arriving at {destination} today (departure city not specified; {DATA_NOTE}):"
    if origin:
        rows, error = _fetch({"dep_iata": origin, "arr_iata": destination})
        if error:
            return error
        if rows:
            header = f"Live flights from {origin} to {destination} today ({DATA_NOTE}):"
        else:
            header = (f"No live flights from {origin} to {destination} found today, so these are other flights "
                      f"arriving at {destination} ({DATA_NOTE}):")
    if not origin or not rows:
        rows, error = _fetch({"arr_iata": destination})
        if error:
            return error

    lines = _format(rows, max_results)
    if not lines:
        return f"No live flights arriving at {destination} found today ({DATA_NOTE})."
    return "\n".join([header, *lines])
