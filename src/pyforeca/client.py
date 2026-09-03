from __future__ import annotations

import math
import re
from typing import Any, Self

import aiohttp

from .exceptions import (
    ForecaAuthError,
    ForecaConnectionError,
    ForecaError,
    ForecaRateLimitError,
)
from .models import (
    AirQualityDailyForecast,
    AirQualityForecast,
    CurrentWeather,
    DailyForecast,
    HourlyForecast,
    Location,
    MinutelyForecast,
    Observation,
    UsageMonth,
)

BASE_URL = "https://weatherapi.foreca.net"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

# A location is "<lon>,<lat>" or a numeric Foreca location id. Anything else —
# path separators, "..", query or fragment markers, percent escapes — would
# escape the endpoint path or override the query parameters set below.
_LOCATION_RE = re.compile(r"\A(?:-?\d{1,3}(?:\.\d+)?,-?\d{1,2}(?:\.\d+)?|\d{1,20})\Z")


def format_location(lon: float, lat: float) -> str:
    """Build the location path segment; the API expects longitude first."""
    for name, value, limit in (("longitude", lon, 180.0), ("latitude", lat, 90.0)):
        if not math.isfinite(value) or abs(value) > limit:
            raise ValueError(f"{name} out of range: {value!r}")
    return f"{lon},{lat}"


def _validate_location(location: str) -> str:
    """Reject any location that is not coordinates or a numeric location id."""
    if not _LOCATION_RE.match(location):
        raise ValueError(
            f"Invalid location {location!r}: expected '<lon>,<lat>' or a location id"
        )
    return location


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
        location = _validate_location(location)
        data = await self._get(f"/api/v1/location/{location}")
        return Location.from_api(data)

    async def current(self, location: str) -> CurrentWeather:
        location = _validate_location(location)
        data = await self._get(f"/api/v1/current/{location}")
        return CurrentWeather.from_api(data["current"])

    async def observation_latest(self, location: str) -> Observation | None:
        """Return the latest observation from a nearby station, if any."""
        data = await self._get(
            f"/api/v1/observation/latest/{_validate_location(location)}"
        )
        observations = data.get("observations") or []
        return Observation.from_api(observations[0]) if observations else None

    async def forecast_minutely(self, location: str) -> list[MinutelyForecast]:
        """Return one-minute precipitation rates for the next hour."""
        data = await self._get(
            f"/api/v1/forecast/minutely/{_validate_location(location)}"
        )
        return [MinutelyForecast.from_api(item) for item in data["forecast"]]

    async def usage_month(self, month: str) -> UsageMonth:
        """Return this account's request counts for a month ("YYYY-MM")."""
        data = await self._get(f"/usage/month/{month}")
        return UsageMonth.from_api(data)

    async def forecast_hourly(
        self, location: str, periods: int = 24, dataset: str = "standard"
    ) -> list[HourlyForecast]:
        data = await self._get(
            f"/api/v1/forecast/hourly/{_validate_location(location)}",
            params={"periods": periods, "dataset": dataset},
        )
        return [HourlyForecast.from_api(item) for item in data["forecast"]]

    async def air_quality_hourly(
        self, location: str, periods: int = 24
    ) -> list[AirQualityForecast]:
        data = await self._get(
            f"/api/v1/air-quality/forecast/hourly/{_validate_location(location)}",
            params={"periods": periods},
        )
        return [AirQualityForecast.from_api(item) for item in data["forecast"]]

    async def air_quality_daily(
        self, location: str, periods: int = 4
    ) -> list[AirQualityDailyForecast]:
        data = await self._get(
            f"/api/v1/air-quality/forecast/daily/{_validate_location(location)}",
            params={"periods": periods},
        )
        return [AirQualityDailyForecast.from_api(item) for item in data["forecast"]]

    async def forecast_daily(
        self, location: str, periods: int = 7, dataset: str = "standard"
    ) -> list[DailyForecast]:
        data = await self._get(
            f"/api/v1/forecast/daily/{_validate_location(location)}",
            params={"periods": periods, "dataset": dataset},
        )
        return [DailyForecast.from_api(item) for item in data["forecast"]]
