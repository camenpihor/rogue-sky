# pylint: disable=protected-access
# requests-mock package creates a pytest fixture, `requests_mock`
import json

import numpy as np
import pytest
import requests

from rogue_sky import darksky, postgres_utilities

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
        ["latitude", "longitude", "queried_date_utc", "weather_date_utc", "weather_json"]
    )
    assert isinstance(json.loads(actual[0]["weather_json"]), dict)
    assert set(json.loads(actual[0]["weather_json"]).keys()) == set(
        darksky.DAILY_WEATHER_MAPPING.keys()
    )


def test_to_database(test_database, parsed_darksky_forecast):
    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    darksky._to_database(
        response=parsed_darksky_forecast, database_url=test_database.pg_url,
    )
    with test_database.get_cursor() as cursor:
        cursor.execute("SELECT * FROM daily_weather_forecast")
        actual = cursor.fetchall()
    assert len(actual) == len(parsed_darksky_forecast)


def test_serialize(parsed_darksky_forecast):
    actual = darksky._serialize(response=parsed_darksky_forecast)
    assert isinstance(actual, dict)
    assert len(actual["daily_forecast"]) == len(parsed_darksky_forecast)
    assert set(actual.keys()) == set(
        ["latitude", "longitude", "queried_date_utc", "daily_forecast"]
    )
    assert set(actual["daily_forecast"][0].keys()) == set(
        darksky.DAILY_WEATHER_MAPPING.keys()
    )


def test_get_weather_forecast(requests_mock, test_database, darksky_json_response):
    requests_mock.get(TEST_URL, json=darksky_json_response)
    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    actual = darksky.get_weather_forecast(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        api_key=API_KEY,
        database_url=test_database.pg_url,
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
        ["latitude", "longitude", "queried_date_utc", "weather_date_utc", "weather_json"]
    )
    assert isinstance(actual[0]["weather_json"], str)

    # tests parse_local_unix_date()
    assert actual[0]["weather_date_utc"] == "2019-11-10"

    # tests weather_json is json
    weather_json = json.loads(actual[0]["weather_json"])
    assert isinstance(weather_json, dict)
    assert set(weather_json.keys()) == set(darksky.DAILY_WEATHER_MAPPING.keys())

    # tests parse()
    assert weather_json["weather_date_utc"] == "2019-11-10"
    assert weather_json["sunrise_time_utc"] == "2019-11-10T15:09:00+00:00"
    assert weather_json["sunset_time_utc"] == "2019-11-11T00:41:00+00:00"
    assert weather_json["temperature_min_time_utc"] == "2019-11-11T08:00:00+00:00"
    assert weather_json["temperature_max_time_utc"] == "2019-11-10T21:56:00+00:00"
    assert weather_json["precip_type"] is None


def test_from_database(test_database, parsed_darksky_forecast):
    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    darksky._to_database(
        response=parsed_darksky_forecast, database_url=test_database.pg_url
    )

    actual = darksky._from_database(
        latitude=47.6062,
        longitude=-122.3321,
        queried_date_utc="2019-12-08",
        database_url=test_database.pg_url,
    )
    assert (
        actual == parsed_darksky_forecast
    ), "outputs from `_from_darksky` and `_from_database` are not the same"


def test_from_database_round_coordinates(test_database, parsed_darksky_forecast):
    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    darksky._to_database(
        response=parsed_darksky_forecast, database_url=test_database.pg_url
    )

    actual = darksky._from_database(
        latitude=47.61,  # round latitude to 2 decimal places
        longitude=-122.33,  # round longitude to 2 decimal places
        queried_date_utc="2019-12-08",
        database_url=test_database.pg_url,
    )
    assert (
        actual == parsed_darksky_forecast
    ), "outputs from `_from_darksky` and `_from_database` are not the same"


def test_parse_address():
    latitude, longitude = (47.6062, -122.3321)
    actual = darksky.parse_address(f"{latitude}, {longitude}")
    assert actual == (latitude, longitude)

    actual = darksky.parse_address(f"{latitude},{longitude}")
    assert actual == (latitude, longitude)

    actual = darksky.parse_address("Seattle, WA")
    np.testing.assert_array_almost_equal(actual, (latitude, longitude), decimal=2)
