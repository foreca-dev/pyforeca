# pyforeca

[![CI](https://github.com/foreca-dev/pyforeca/actions/workflows/ci.yml/badge.svg)](https://github.com/foreca-dev/pyforeca/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Async Python client for the [Foreca Weather API](https://developer.foreca.com) —
current conditions, hourly and daily forecasts, air quality and location lookup,
with typed models and `aiohttp` under the hood.

## Getting an API key

Create a free account at [developer.foreca.com](https://developer.foreca.com), pick a plan,
and copy your key from **My API**. The Freemium plan is free for non-commercial use
(hobbyist, student, and research projects); commercial use, a larger quota, or the rest of
Foreca's weather products need a [paid plan](https://business.foreca.com/weather-api/pricing).

## Install

```bash
pip install pyforeca
```

## Usage

```python
import asyncio
from pyforeca import ForecaApiClient, format_location

async def main() -> None:
    async with ForecaApiClient("YOUR_API_KEY") as client:
        location = format_location(lon=24.94, lat=60.17)

        current = await client.current(location)
        print(current.temperature, current.symbol_phrase)

        daily = await client.forecast_daily(location, periods=7)
        hourly = await client.forecast_hourly(location, periods=24)
        air_quality = await client.air_quality_hourly(location, periods=1)

asyncio.run(main())
```

Pass an existing `aiohttp.ClientSession` as `session=` to share one with your
application; the client then leaves closing it to you.

| Method | Endpoint |
|---|---|
| `location_info(location)` | `/api/v1/location/{location}` |
| `current(location)` | `/api/v1/current/{location}` |
| `observation_latest(location)` | `/api/v1/observation/latest/{location}` |
| `forecast_minutely(location)` | `/api/v1/forecast/minutely/{location}` |
| `forecast_hourly(location, periods, dataset)` | `/api/v1/forecast/hourly/{location}` |
| `forecast_daily(location, periods, dataset)` | `/api/v1/forecast/daily/{location}` |
| `air_quality_hourly(location, periods)` | `/api/v1/air-quality/forecast/hourly/{location}` |
| `air_quality_daily(location, periods)` | `/api/v1/air-quality/forecast/daily/{location}` |

`location` is `"longitude,latitude"` (longitude first) or a Foreca location id.
`Symbol.parse("d421")` decodes weather symbol codes; see the
[symbol reference](https://developer.foreca.com/resources).

Errors: `ForecaAuthError` (key rejected), `ForecaRateLimitError` (HTTP 429),
`ForecaConnectionError` (network/timeout), all subclasses of `ForecaError`.

## Attribution

Applications displaying Foreca data must attribute Foreca — see the
[logo and attribution requirements](https://business.foreca.com/logo).

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -e . pytest pytest-asyncio
.venv/bin/pytest
```

Maintained by [Foreca](https://business.foreca.com) in the
[foreca-dev](https://github.com/foreca-dev) organization. Released under the
[MIT License](LICENSE).
