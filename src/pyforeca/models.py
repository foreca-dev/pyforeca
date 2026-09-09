from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from typing import Any, Self

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z0-9])")


def _to_snake(name: str) -> str:
    return _CAMEL_RE.sub("_", name).lower().replace("_string", "_str")


class _ApiModel:
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        known = {f.name for f in fields(cls)}  # type: ignore[arg-type]
        kwargs = {}
        for key, value in data.items():
            snake = _to_snake(key)
            if snake in known:
                kwargs[snake] = value
        return cls(**kwargs)  # type: ignore[call-arg]


@dataclass(slots=True)
class Location(_ApiModel):
    id: int | None = None
    name: str | None = None
    country: str | None = None
    timezone: str | None = None
    lon: float | None = None
    lat: float | None = None
    admin_area: str | None = None


@dataclass(slots=True)
class CurrentWeather(_ApiModel):
    time: str | None = None
    symbol: str | None = None
    symbol_phrase: str | None = None
    temperature: float | None = None
    feels_like_temp: float | None = None
    rel_humidity: float | None = None
    dew_point: float | None = None
    wind_speed: float | None = None
    wind_dir: float | None = None
    wind_dir_str: str | None = None
    wind_gust: float | None = None
    precip_prob: int | None = None
    precip_rate: float | None = None
    cloudiness: int | None = None
    thunder_prob: float | None = None
    uv_index: float | None = None
    pressure: float | None = None
    visibility: float | None = None


@dataclass(slots=True)
class MinutelyForecast(_ApiModel):
    time: str | None = None
    precip_rate: float | None = None


@dataclass(slots=True)
class Observation(_ApiModel):
    time: str | None = None
    station: str | None = None
    distance: str | None = None
    elevation: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    symbol: str | None = None
    temperature: float | None = None
    feels_like_temp: float | None = None
    rel_humidity: float | None = None
    pressure: float | None = None
    visibility: float | None = None
    wind_speed: float | None = None
    wind_dir: float | None = None
    wind_dir_str: str | None = None
    wind_gust: float | None = None
    snow_depth: float | None = None


@dataclass(slots=True)
class HourlyForecast(_ApiModel):
    time: str | None = None
    symbol: str | None = None
    symbol_phrase: str | None = None
    temperature: float | None = None
    feels_like_temp: float | None = None
    wind_speed: float | None = None
    wind_gust: float | None = None
    rel_humidity: float | None = None
    dew_point: float | None = None
    wind_dir: float | None = None
    wind_dir_str: str | None = None
    precip_prob: int | None = None
    precip_accum: float | None = None
    snow_accum: float | None = None
    cloudiness: int | None = None
    thunder_prob: float | None = None
    uv_index: float | None = None
    pressure: float | None = None
    visibility: float | None = None
    precip_type: str | None = None
    solar_radiation: float | None = None
    snow_depth: float | None = None


@dataclass(slots=True)
class DailyForecast(_ApiModel):
    date: str | None = None
    symbol: str | None = None
    symbol_phrase: str | None = None
    max_temp: float | None = None
    min_temp: float | None = None
    max_feels_like_temp: float | None = None
    min_feels_like_temp: float | None = None
    precip_accum: float | None = None
    precip_prob: int | None = None
    max_wind_speed: float | None = None
    max_wind_gust: float | None = None
    wind_dir: float | None = None
    uv_index: float | None = None
    pressure: float | None = None
    cloudiness: int | None = None
    max_rel_humidity: float | None = None
    min_rel_humidity: float | None = None
    snow_accum: float | None = None
    snow_depth: float | None = None
    sunrise: str | None = None
    sunset: str | None = None
    sunrise_epoch: int | None = None
    sunset_epoch: int | None = None
    sunhours: float | None = None
    solar_radiation_sum: float | None = None
    confidence: str | None = None
    moon_phase: float | None = None
    moonrise: str | None = None
    moonset: str | None = None
    min_visibility: float | None = None
    max_dew_point: float | None = None
    min_dew_point: float | None = None


_AQ_FIELD_MAP = {
    "time": "time",
    "pollutant": "pollutant",
    "pollutantPhrase": "pollutant_phrase",
    "AQI": "aqi",
    "AQI_CO": "aqi_co",
    "AQI_NO2": "aqi_no2",
    "AQI_O3": "aqi_o3",
    "AQI_SO2": "aqi_so2",
    "AQI_PM10": "aqi_pm10",
    "AQI_PM2P5": "aqi_pm2p5",
}


@dataclass(slots=True)
class AirQualityForecast:
    time: str | None = None
    pollutant: str | None = None
    pollutant_phrase: str | None = None
    aqi: float | None = None
    aqi_co: float | None = None
    aqi_no2: float | None = None
    aqi_o3: float | None = None
    aqi_so2: float | None = None
    aqi_pm10: float | None = None
    aqi_pm2p5: float | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AirQualityForecast:
        return cls(
            **{
                snake: data[key]
                for key, snake in _AQ_FIELD_MAP.items()
                if key in data
            }
        )


_AQ_DAILY_FIELD_MAP = {
    "date": "date",
    "pollutant": "pollutant",
    "pollutantPhrase": "pollutant_phrase",
    "AQI": "aqi",
    "AQI_CO": "aqi_co",
    "AQI_NO2": "aqi_no2",
    "AQI_GO3": "aqi_o3",
    "AQI_SO2": "aqi_so2",
    "AQI_PM10": "aqi_pm10",
    "AQI_PM2P5": "aqi_pm2p5",
}


@dataclass(slots=True)
class AirQualityDailyForecast:
    date: str | None = None
    pollutant: str | None = None
    pollutant_phrase: str | None = None
    aqi: float | None = None
    aqi_co: float | None = None
    aqi_no2: float | None = None
    aqi_o3: float | None = None
    aqi_so2: float | None = None
    aqi_pm10: float | None = None
    aqi_pm2p5: float | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AirQualityDailyForecast:
        return cls(
            **{
                snake: data[key]
                for key, snake in _AQ_DAILY_FIELD_MAP.items()
                if key in data
            }
        )


def _usage_hits(entry: dict[str, Any]) -> float | None:
    """Read a request count that the API may only give per API product.

    The month carries a top-level total, but each day in the breakdown carries
    only an "apis" list, so the day's total has to be summed from it.
    """
    hits = entry.get("hits")
    if hits is not None:
        return hits
    apis = entry.get("apis")
    if not apis:
        return None
    return sum(api.get("hits") or 0 for api in apis)


@dataclass(slots=True)
class UsageDay:
    date: str | None = None
    hits: float | None = None


@dataclass(slots=True)
class UsageMonth:
    hits: float | None = None
    daily: list[UsageDay] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> UsageMonth:
        return cls(
            hits=_usage_hits(data),
            daily=[
                UsageDay(date=day.get("date"), hits=_usage_hits(day))
                for day in data.get("daily") or []
            ],
        )

    def hits_on(self, date: str) -> float:
        """Return the request count for an ISO date, zero if the day has none."""
        for day in self.daily:
            if day.date == date:
                return day.hits or 0
        return 0


@dataclass(slots=True, frozen=True)
class Symbol:
    """Decoded Foreca weather symbol code (e.g. "d421").

    cloudiness: 0 clear, 1 almost clear, 2 half cloudy, 3 broken,
        4 overcast, 5 thin high clouds, 6 fog
    precip_rate: 0 none, 1 slight, 2 showers, 3 continuous, 4 thunder
    precip_type: 0 rain, 1 sleet, 2 snow
    """

    is_day: bool
    cloudiness: int
    precip_rate: int
    precip_type: int

    @classmethod
    def parse(cls, code: str) -> Symbol | None:
        if not code or len(code) != 4 or code[0] not in "dn" or not code[1:].isdigit():
            return None
        return cls(
            is_day=code[0] == "d",
            cloudiness=int(code[1]),
            precip_rate=int(code[2]),
            precip_type=int(code[3]),
        )
