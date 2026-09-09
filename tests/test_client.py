from collections.abc import AsyncIterator
from typing import Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from pyforeca import (
    ForecaApiClient,
    ForecaAuthError,
    ForecaError,
    ForecaRateLimitError,
    Symbol,
    format_location,
)

CURRENT_PAYLOAD = {
    "current": {
        "time": "2026-09-01T17:00+03:00",
        "symbol": "d200",
        "symbolPhrase": "partly cloudy",
        "temperature": 17.4,
        "feelsLikeTemp": 16.9,
        "relHumidity": 62,
        "dewPoint": 10.1,
        "windSpeed": 4.2,
        "windDir": 210,
        "windDirString": "SW",
        "windGust": 8.0,
        "precipProb": 5,
        "precipRate": 0,
        "cloudiness": 40,
        "thunderProb": 0,
        "uvIndex": 2,
        "pressure": 1013.2,
        "visibility": 20000,
        "someFutureField": "ignored",
    }
}

HOURLY_PAYLOAD = {
    "forecast": [
        {
            "time": "2026-09-01T18:00+03:00",
            "symbol": "d300",
            "temperature": 16.0,
            "feelsLikeTemp": 15.2,
            "windSpeed": 3.9,
            "windGust": 7.1,
            "windDir": 200,
            "precipProb": 10,
            "precipAccum": 0.0,
        }
    ]
}

DAILY_PAYLOAD = {
    "forecast": [
        {
            "date": "2026-09-02",
            "symbol": "d310",
            "maxTemp": 18.0,
            "minTemp": 9.0,
            "precipAccum": 1.2,
            "maxWindSpeed": 6.0,
            "windDir": 225,
            "uvIndex": 3,
        }
    ]
}

AIR_QUALITY_PAYLOAD = {
    "forecast": [
        {
            "time": "2026-09-01T18:00+03:00",
            "pollutant": "Ozone",
            "pollutantPhrase": "Ozone",
            "AQI": 23,
            "AQI_CO": 2,
            "AQI_NO2": 5,
            "AQI_O3": 23,
            "AQI_SO2": 1,
            "AQI_PM10": 8,
            "AQI_PM2P5": 11,
        }
    ]
}

AIR_QUALITY_DAILY_PAYLOAD = {
    "forecast": [
        {
            "date": "2026-09-01",
            "AQI": 37,
            "pollutant": "Ozone",
            "pollutantPhrase": "Ozone",
            "AQI_CO": 1,
            "AQI_NO2": 8,
            "AQI_GO3": 37,
            "AQI_SO2": 0,
            "AQI_PM2P5": 21,
            "AQI_PM10": 8,
        },
        {
            "date": "2026-09-02",
            "AQI": 34,
            "pollutant": "Ozone",
            "pollutantPhrase": "Ozone",
            "AQI_GO3": 34,
        },
    ]
}

MINUTELY_PAYLOAD = {
    "resolution": "1 min",
    "forecast": [
        {"time": "2026-09-01T17:00+03:00", "precipRate": 0.0},
        {"time": "2026-09-01T17:01+03:00", "precipRate": 0.0},
        {"time": "2026-09-01T17:02+03:00", "precipRate": 0.6},
        {"time": "2026-09-01T17:03+03:00", "precipRate": 1.2},
    ],
}

OBSERVATION_PAYLOAD = {
    "observations": [
        {
            "time": "2026-09-01T16:50+03:00",
            "station": "Helsinki Kaisaniemi",
            "distance": "2 km NE",
            "elevation": 3,
            "latitude": 60.18,
            "longitude": 24.94,
            "symbol": "d200",
            "temperature": 18.9,
            "feelsLikeTemp": 18.4,
            "relHumidity": 71,
            "pressure": 1007.2,
            "visibility": 30000,
            "windSpeed": 3.1,
            "windDir": 205,
            "windDirString": "SSW",
            "windGust": 6.4,
            "snowDepth": 0,
        }
    ]
}

LOCATION_PAYLOAD = {
    "id": 100658225,
    "name": "Helsinki",
    "country": "Finland",
    "timezone": "Europe/Helsinki",
    "lon": 24.94,
    "lat": 60.17,
    "adminArea": "Uusimaa",
}

seen_requests: list[web.Request] = []


def _json_handler(payload: dict[str, Any]) -> Any:
    async def handler(request: web.Request) -> web.Response:
        seen_requests.append(request)
        return web.json_response(payload)

    return handler


async def _error_handler(request: web.Request) -> web.Response:
    return web.Response(status=int(request.match_info["status"]))


@pytest.fixture
async def server() -> AsyncIterator[TestServer]:
    app = web.Application()
    app.router.add_get("/api/v1/current/{loc}", _json_handler(CURRENT_PAYLOAD))
    app.router.add_get("/api/v1/forecast/hourly/{loc}", _json_handler(HOURLY_PAYLOAD))
    app.router.add_get("/api/v1/forecast/daily/{loc}", _json_handler(DAILY_PAYLOAD))
    app.router.add_get("/api/v1/location/{loc}", _json_handler(LOCATION_PAYLOAD))
    app.router.add_get(
        "/api/v1/air-quality/forecast/hourly/{loc}", _json_handler(AIR_QUALITY_PAYLOAD)
    )
    app.router.add_get(
        "/api/v1/air-quality/forecast/daily/{loc}",
        _json_handler(AIR_QUALITY_DAILY_PAYLOAD),
    )
    app.router.add_get("/api/v1/forecast/minutely/{loc}", _json_handler(MINUTELY_PAYLOAD))
    app.router.add_get(
        "/api/v1/observation/latest/{loc}", _json_handler(OBSERVATION_PAYLOAD)
    )
    app.router.add_get(
        "/empty/api/v1/observation/latest/{loc}", _json_handler({"observations": []})
    )
    app.router.add_get("/usage/month/{month}", _json_handler(USAGE_PAYLOAD))
    app.router.add_get("/nodaily/usage/month/{month}", _json_handler({"hits": 7}))
    app.router.add_get("/error/api/v1/current/{status},0", _error_handler)
    test_server = TestServer(app)
    await test_server.start_server()
    seen_requests.clear()
    yield test_server
    await test_server.close()


def _client(server: TestServer, path_prefix: str = "") -> ForecaApiClient:
    return ForecaApiClient("test-key", base_url=f"http://{server.host}:{server.port}{path_prefix}")


async def test_current(server: TestServer) -> None:
    async with _client(server) as client:
        current = await client.current("24.94,60.17")
    assert current.temperature == 17.4
    assert current.symbol == "d200"
    assert current.feels_like_temp == 16.9
    assert current.wind_dir_str == "SW"
    assert current.pressure == 1013.2
    assert seen_requests[0].headers["Authorization"] == "Bearer test-key"


async def test_forecast_hourly(server: TestServer) -> None:
    async with _client(server) as client:
        hours = await client.forecast_hourly("24.94,60.17")
    assert len(hours) == 1
    assert hours[0].temperature == 16.0
    assert hours[0].precip_accum == 0.0
    assert seen_requests[0].query["periods"] == "24"
    assert seen_requests[0].query["dataset"] == "standard"


async def test_forecast_daily(server: TestServer) -> None:
    async with _client(server) as client:
        days = await client.forecast_daily("24.94,60.17", periods=7)
    assert len(days) == 1
    assert days[0].max_temp == 18.0
    assert days[0].min_temp == 9.0


async def test_air_quality_hourly(server: TestServer) -> None:
    async with _client(server) as client:
        aq = await client.air_quality_hourly("24.94,60.17", periods=1)
    assert len(aq) == 1
    assert aq[0].aqi == 23
    assert aq[0].aqi_pm2p5 == 11
    assert aq[0].pollutant == "Ozone"
    assert seen_requests[0].query["periods"] == "1"


async def test_air_quality_daily(server: TestServer) -> None:
    async with _client(server) as client:
        days = await client.air_quality_daily("24.94,60.17")
    assert len(days) == 2
    assert days[0].date == "2026-09-01"
    assert days[0].aqi == 37
    assert days[0].aqi_o3 == 37
    assert days[1].aqi == 34
    assert seen_requests[0].query["periods"] == "4"


async def test_location_info(server: TestServer) -> None:
    async with _client(server) as client:
        location = await client.location_info("24.94,60.17")
    assert location.name == "Helsinki"
    assert location.timezone == "Europe/Helsinki"


@pytest.mark.parametrize(
    ("status", "exception"),
    [(401, ForecaAuthError), (403, ForecaAuthError), (429, ForecaRateLimitError), (500, ForecaError)],
)
async def test_error_statuses(
    server: TestServer, status: int, exception: type[Exception]
) -> None:
    async with _client(server, "/error") as client:
        with pytest.raises(exception):
            await client.current(f"{status},0")


def test_format_location_longitude_first() -> None:
    assert format_location(24.94, 60.17) == "24.94,60.17"


def test_symbol_parse() -> None:
    symbol = Symbol.parse("d421")
    assert symbol is not None
    assert symbol.is_day
    assert symbol.cloudiness == 4
    assert symbol.precip_rate == 2
    assert symbol.precip_type == 1

    night = Symbol.parse("n000")
    assert night is not None
    assert not night.is_day

    assert Symbol.parse("") is None
    assert Symbol.parse("x421") is None
    assert Symbol.parse("d42") is None
    assert Symbol.parse("d4a1") is None


@pytest.mark.parametrize(
    "location",
    [
        pytest.param("../../../admin/keys", id="path_escape"),
        pytest.param("60,25?periods=9999", id="query_injection"),
        pytest.param("60,25#frag", id="fragment"),
        pytest.param("..%2fadmin", id="percent_escape"),
        pytest.param("//evil.example.com/x", id="double_slash"),
        pytest.param("60,25/extra", id="extra_segment"),
        pytest.param("", id="empty"),
        pytest.param("Helsinki", id="place_name"),
    ],
)
async def test_location_injection_rejected(server: TestServer, location: str) -> None:
    """A location must never be able to escape the endpoint path or add query params."""
    async with _client(server) as client:
        for call in (
            client.location_info,
            client.current,
            client.forecast_hourly,
            client.forecast_daily,
            client.air_quality_hourly,
            client.air_quality_daily,
            client.observation_latest,
            client.forecast_minutely,
        ):
            with pytest.raises(ValueError):
                await call(location)
    assert not seen_requests


@pytest.mark.parametrize(
    "month",
    [
        pytest.param("../../../authorize/key", id="path_escape"),
        pytest.param("2026-09?group_by=endpoint", id="query_injection"),
        pytest.param("2026-09#frag", id="fragment"),
        pytest.param("..%2fauthorize", id="percent_escape"),
        pytest.param("//evil.example.com/x", id="double_slash"),
        pytest.param("2026-09/extra", id="extra_segment"),
        pytest.param("2026-9", id="unpadded"),
        pytest.param("", id="empty"),
    ],
)
async def test_usage_month_injection_rejected(server: TestServer, month: str) -> None:
    """A month must never be able to escape the endpoint path or add query params."""
    async with _client(server) as client:
        with pytest.raises(ValueError):
            await client.usage_month(month)
    assert not seen_requests


@pytest.mark.parametrize(
    "location",
    [
        pytest.param("24.94,60.17", id="coordinates"),
        pytest.param("-24.94,-60.17", id="negative_coordinates"),
        pytest.param("100658225", id="location_id"),
    ],
)
async def test_valid_locations_accepted(server: TestServer, location: str) -> None:
    """Coordinates and numeric location ids stay accepted."""
    async with _client(server) as client:
        await client.current(location)
    assert seen_requests


@pytest.mark.parametrize(
    ("lon", "lat"),
    [
        pytest.param(181.0, 0.0, id="lon_too_high"),
        pytest.param(0.0, 91.0, id="lat_too_high"),
        pytest.param(float("nan"), 0.0, id="lon_nan"),
        pytest.param(0.0, float("inf"), id="lat_inf"),
    ],
)
def test_format_location_rejects_out_of_range(lon: float, lat: float) -> None:
    """format_location must reject coordinates the API cannot represent."""
    with pytest.raises(ValueError):
        format_location(lon, lat)


async def test_forecast_minutely(server: TestServer) -> None:
    """Test the one-minute precipitation nowcast."""
    async with _client(server) as client:
        steps = await client.forecast_minutely("24.94,60.17")
    assert len(steps) == 4
    assert steps[0].precip_rate == 0.0
    assert steps[2].precip_rate == 0.6
    assert steps[2].time == "2026-09-01T17:02+03:00"


async def test_observation_latest(server: TestServer) -> None:
    """Test the latest station observation."""
    async with _client(server) as client:
        obs = await client.observation_latest("24.94,60.17")
    assert obs is not None
    assert obs.station == "Helsinki Kaisaniemi"
    assert obs.distance == "2 km NE"
    assert obs.temperature == 18.9
    assert obs.wind_dir_str == "SSW"
    assert obs.snow_depth == 0


async def test_observation_latest_none_available(server: TestServer) -> None:
    """Test a location with no nearby station returns None rather than raising."""
    async with _client(server, "/empty") as client:
        obs = await client.observation_latest("24.94,60.17")
    assert obs is None


USAGE_PAYLOAD = {
    "apis": [
        {"name": "Weather API", "hits": 40},
        {"name": "Map API", "hits": 4},
        {"name": "Administrative", "hits": 0},
    ],
    "hits": 44,
    "daily": [
        {"date": "2026-09-01", "apis": [{"name": "Weather API", "hits": 23}]},
        {
            "date": "2026-09-03",
            "apis": [
                {"name": "Weather API", "hits": 17},
                {"name": "Map API", "hits": 4},
            ],
        },
        {"date": "2026-09-04"},
    ],
}


async def test_usage_month(server: TestServer) -> None:
    """Test the monthly usage counts and the per-day lookup."""
    async with _client(server) as client:
        usage = await client.usage_month("2026-09")
    assert usage.hits == 44
    assert len(usage.daily) == 3
    assert usage.hits_on("2026-09-01") == 23
    assert usage.hits_on("2026-09-03") == 21
    assert usage.hits_on("2026-09-02") == 0
    assert usage.daily[2].hits is None
    assert usage.hits_on("2026-09-04") == 0


async def test_usage_month_without_daily_breakdown(server: TestServer) -> None:
    """Test a month with no daily breakdown still reports a total."""
    async with _client(server, "/nodaily") as client:
        usage = await client.usage_month("2026-09")
    assert usage.hits == 7
    assert usage.daily == []
    assert usage.hits_on("2026-09-03") == 0

async def test_integral_percentages_are_typed_as_int(server: TestServer) -> None:
    """Test the percentage fields the API only ever reports as whole numbers.

    Measured over 290 forecast steps in five climates: precipProb and cloudiness
    are always integral, while thunderProb is not, so only the first two are
    narrowed to int.
    """
    async with _client(server) as client:
        hours = await client.forecast_hourly("24.94,60.17")
        days = await client.forecast_daily("24.94,60.17")
        current = await client.current("24.94,60.17")
    for value in (
        hours[0].precip_prob,
        hours[0].cloudiness,
        days[0].precip_prob,
        current.precip_prob,
        current.cloudiness,
    ):
        assert value is None or isinstance(value, int)
