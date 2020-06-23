# pylint: disable=protected-access
# requests-mock package creates a pytest fixture, `requests_mock`
import json

import pytest
import requests

from rogue_sky import darksky

API_KEY = "TEST"
LATITUDE = 1.0
LONGITUDE = 2.0
TEST_URL = darksky.DARKSKY_URL.format(
    api_key=API_KEY, latitude=LATITUDE, longitude=LONGITUDE
)


def test_make_request(requests_mock):
    requests_mock.get(TEST_URL)
    actual = darksky._make_request(
        api_key=API_KEY,
        latitude=LATITUDE,
        longitude=LONGITUDE,
        queried_date_utc="2019-01-01",
    )
    assert actual.status_code == 200


def test_make_request_fail(requests_mock):
    requests_mock.get(TEST_URL, status_code=404)
    with pytest.raises(requests.exceptions.HTTPError) as error:
        darksky._make_request(
            api_key=API_KEY,
            latitude=LATITUDE,
            longitude=LONGITUDE,
            queried_date_utc="2019-01-01",
        )
    assert API_KEY not in str(error.value)


def test_from_darksky(requests_mock, darksky_json_response):
    requests_mock.get(TEST_URL, json=darksky_json_response)
    actual = darksky._from_darksky(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        queried_date_utc="2019-01-01",
        api_key=API_KEY,
    )
    assert isinstance(actual, list)
    assert isinstance(actual[0], dict)
    assert set(actual[0].keys()) == set(
        [
            "latitude",
            "longitude",
            "queried_date_utc",
            "timezone",
            "weather_date_local",
            "weather_json",
        ]
    )
    assert isinstance(json.loads(actual[0]["weather_json"]), dict)
    assert set(json.loads(actual[0]["weather_json"]).keys()) == set(
        darksky.DAILY_WEATHER_MAPPING.keys()
    )


def test_serialize(parsed_darksky_forecast):
    actual = darksky._serialize(response=parsed_darksky_forecast)
    assert isinstance(actual, dict)
    assert len(actual["daily_forecast"]) == len(parsed_darksky_forecast)
    assert set(actual.keys()) == set(
        ["latitude", "longitude", "queried_date_utc", "timezone", "daily_forecast"]
    )
    assert set(actual["daily_forecast"][0].keys()) == set(
        darksky.DAILY_WEATHER_MAPPING.keys()
    )


def test_get_weather_forecast(requests_mock, darksky_json_response):
    requests_mock.get(TEST_URL, json=darksky_json_response)
    actual = darksky.get_weather_forecast(
        latitude=LATITUDE, longitude=LONGITUDE, api_key=API_KEY,
    )
    assert len(actual["daily_forecast"]) == len(darksky_json_response["daily"]["data"])
    assert isinstance(actual, dict)
    assert set(actual["daily_forecast"][0].keys()) == set(
        darksky.DAILY_WEATHER_MAPPING.keys()
    )


def test_parse_darksky_response(darksky_json_response):
    actual = darksky._parse_darksky_response(
        response_json=darksky_json_response, queried_date_utc="2019-10-10"
    )
    assert isinstance(actual, list)
    assert len(actual) == len(darksky_json_response["daily"]["data"])
    assert set(actual[0].keys()) == set(
        [
            "latitude",
            "longitude",
            "queried_date_utc",
            "timezone",
            "weather_date_local",
            "weather_json",
        ]
    )
    assert isinstance(actual[0]["weather_json"], str)

    # tests parse_local_unix_date()
    assert actual[0]["weather_date_local"] == "2019-11-10"

    # tests weather_json is json
    weather_json = json.loads(actual[0]["weather_json"])
    assert isinstance(weather_json, dict)
    assert set(weather_json.keys()) == set(darksky.DAILY_WEATHER_MAPPING.keys())

    # tests parse()
    assert weather_json["weather_date_local"] == "2019-11-10"
    assert weather_json["sunrise_time_local"] == "2019-11-10T07:09:00-08:00"
    assert weather_json["sunset_time_local"] == "2019-11-10T16:41:00-08:00"
    assert weather_json["precip_type"] is None
