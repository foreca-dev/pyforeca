# pyforeca

Async Python client for the [Foreca Weather API](https://developer.foreca.com).

Get an API key by creating a free account at [developer.foreca.com](https://developer.foreca.com).

```python
import asyncio
from pyforeca import ForecaApiClient, format_location

async def main():
    async with ForecaApiClient("YOUR_API_KEY") as client:
        location = format_location(lon=24.94, lat=60.17)
        current = await client.current(location)
        print(current.temperature, current.symbol_phrase)
        daily = await client.forecast_daily(location, periods=7)
        hourly = await client.forecast_hourly(location, periods=24)

asyncio.run(main())
```

Weather data © Foreca. Applications displaying this data must attribute Foreca
per the [API terms](https://developer.foreca.com).

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -e . pytest pytest-asyncio
.venv/bin/pytest
```
