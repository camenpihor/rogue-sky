# pylint: disable=protected-access
import requests_mock

from rogue_sky import darksky, stars


def test_serialize(parsed_star_visbility_forecast, serialized_weather_forecast):
    actual = stars._serialize(
        predictions=parsed_star_visbility_forecast,
        weather_forecast=serialized_weather_forecast,
    )
    assert isinstance(actual, dict)
    assert len(actual["daily_forecast"]) == len(parsed_star_visbility_forecast)
    assert (
        actual["daily_forecast"][0]["star_visibility"]
        == parsed_star_visbility_forecast[0]["prediction"]
    )
    assert set(actual.keys()) == set(
        [
            "latitude",
            "longitude",
            "queried_date_utc",
            "timezone",
            "daily_forecast",
            "city",
            "state",
        ]
    )

    assert set(actual["daily_forecast"][0].keys()) == set(
        list(darksky.DAILY_WEATHER_MAPPING.keys())
        + ["star_visibility", "moonrise_time_local", "moon_illumination"]
    )


def test_get_star_forecast(darksky_json_response):
    api_key = "test"
    latitude = 47.6062
    longitude = -122.3321
    test_url = darksky.DARKSKY_URL.format(
        api_key=api_key, latitude=latitude, longitude=longitude
    )
    with requests_mock.Mocker(real_http=True) as mock:
        mock.get(test_url, json=darksky_json_response)
        actual = stars.get_star_forecast(
            latitude=latitude, longitude=longitude, api_key=api_key,
        )
    assert len(actual["daily_forecast"]) == len(darksky_json_response["daily"]["data"])
    assert isinstance(actual, dict)
