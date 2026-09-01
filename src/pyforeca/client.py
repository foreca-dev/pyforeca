from __future__ import annotations

from typing import Any, Self

import aiohttp

from .exceptions import (
    ForecaAuthError,
    ForecaConnectionError,
    ForecaError,
    ForecaRateLimitError,
)
from .models import (
    AirQualityForecast,
    CurrentWeather,
    DailyForecast,
    HourlyForecast,
    Location,
)

BASE_URL = "https://weatherapi.foreca.net"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


def format_location(lon: float, lat: float) -> str:
    """Build the location path segment; the API expects longitude first."""
    return f"{lon},{lat}"


class ForecaApiClient:
    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession | None = None,
        base_url: str = BASE_URL,
    ) -> None:
        self._api_key = api_key
        self._session = session
        self._owns_session = session is None
        self._base_url = base_url.rstrip("/")

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        try:
            async with self._session.get(
                f"{self._base_url}{path}",
                params=params,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status in (401, 403):
                    raise ForecaAuthError(f"API key rejected (HTTP {resp.status})")
                if resp.status == 429:
                    raise ForecaRateLimitError("Rate limit exceeded (HTTP 429)")
                if resp.status >= 400:
                    raise ForecaError(f"HTTP {resp.status} for {path}")
                return await resp.json()
        except TimeoutError as err:
            raise ForecaConnectionError(f"Timeout requesting {path}") from err
        except aiohttp.ClientError as err:
            raise ForecaConnectionError(f"Error requesting {path}: {err}") from err

    async def location_info(self, location: str) -> Location:
        data = await self._get(f"/api/v1/location/{location}")
        return Location.from_api(data)

    async def current(self, location: str) -> CurrentWeather:
        data = await self._get(f"/api/v1/current/{location}")
        return CurrentWeather.from_api(data["current"])

    async def forecast_hourly(
        self, location: str, periods: int = 24, dataset: str = "standard"
    ) -> list[HourlyForecast]:
        data = await self._get(
            f"/api/v1/forecast/hourly/{location}",
            params={"periods": periods, "dataset": dataset},
        )
        return [HourlyForecast.from_api(item) for item in data["forecast"]]

    async def air_quality_hourly(
        self, location: str, periods: int = 24
    ) -> list[AirQualityForecast]:
        data = await self._get(
            f"/api/v1/air-quality/forecast/hourly/{location}",
            params={"periods": periods},
        )
        return [AirQualityForecast.from_api(item) for item in data["forecast"]]

    async def forecast_daily(
        self, location: str, periods: int = 7, dataset: str = "standard"
    ) -> list[DailyForecast]:
        data = await self._get(
            f"/api/v1/forecast/daily/{location}",
            params={"periods": periods, "dataset": dataset},
        )
        return [DailyForecast.from_api(item) for item in data["forecast"]]
