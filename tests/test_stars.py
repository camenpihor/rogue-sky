# pylint: disable=protected-access
# requests-mock package creates a pytest fixture, `requests_mock`
import json

import numpy as np
import pytest
import requests

from rogue_sky import darksky, stars


def test_predict_visibility():
    actual = stars.predict_visibility(np.array([1, 0, np.nan]))
    np.testing.assert_array_equal(actual, np.array([0, 1, np.nan]))


def test_from_weather(requests_mock, serialized_weather_forecast):
    actual = stars._from_weather(weather_forecast=serialized_weather_forecast)
    assert isinstance(actual, list)
    assert isinstance(actual[0], dict)
    assert set(actual[0].keys()) == set(
        ["latitude", "longitude", "queried_date_utc", "weather_date_local", "prediction"]
    )


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
        + ["star_visibility", "moonrise_time_local"]
    )


def test_get_star_forecast(requests_mock, darksky_json_response):
    api_key = "test"
    latitude = 47.6062
    longitude = -122.3321
    test_url = darksky.DARKSKY_URL.format(
        api_key=api_key, latitude=latitude, longitude=longitude
    )
    requests_mock.get(test_url, json=darksky_json_response)
    actual = stars.get_star_forecast(
        latitude=latitude, longitude=longitude, api_key=api_key,
    )
    assert len(actual["daily_forecast"]) == len(darksky_json_response["daily"]["data"])
    assert isinstance(actual, dict)
