# pylint: disable=protected-access
# requests-mock package creates a pytest fixture, `requests_mock`
import json

import numpy as np
import pytest
import requests

from rogue_sky import darksky, postgres_utilities, stars


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


def test_to_database(test_database, parsed_star_visbility_forecast):
    postgres_utilities.create_star_table(pg_url=test_database.pg_url)
    stars._to_database(
        predictions=parsed_star_visbility_forecast, database_url=test_database.pg_url,
    )
    with test_database.get_cursor() as cursor:
        cursor.execute("SELECT * FROM daily_star_visibility_forecast")
        actual = cursor.fetchall()
    assert len(actual) == len(parsed_star_visbility_forecast)


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
        ["latitude", "longitude", "queried_date_utc", "daily_forecast", "city", "state"]
    )
    assert set(actual["daily_forecast"][0].keys()) == set(
        list(darksky.DAILY_WEATHER_MAPPING.keys()) + ["star_visibility"]
    )


def test_get_star_forecast(requests_mock, test_database, darksky_json_response):
    api_key = "test"
    latitude = 47.6062
    longitude = -122.3321
    test_url = darksky.DARKSKY_URL.format(
        api_key=api_key, latitude=latitude, longitude=longitude
    )
    requests_mock.get(test_url, json=darksky_json_response)
    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    postgres_utilities.create_star_table(pg_url=test_database.pg_url)
    actual = stars.get_star_forecast(
        latitude=latitude,
        longitude=longitude,
        api_key=api_key,
        database_url=test_database.pg_url,
    )
    assert len(actual["daily_forecast"]) == len(darksky_json_response["daily"]["data"])
    assert isinstance(actual, dict)


def test_from_database(test_database, parsed_star_visbility_forecast):
    postgres_utilities.create_star_table(pg_url=test_database.pg_url)
    stars._to_database(
        predictions=parsed_star_visbility_forecast, database_url=test_database.pg_url
    )

    actual = stars._from_database(
        latitude=47.6062,
        longitude=-122.3321,
        queried_date_utc="2019-12-09",
        database_url=test_database.pg_url,
    )
    assert actual == parsed_star_visbility_forecast


def test_from_database_round_coordinates(test_database, parsed_star_visbility_forecast):
    postgres_utilities.create_star_table(pg_url=test_database.pg_url)
    stars._to_database(
        predictions=parsed_star_visbility_forecast, database_url=test_database.pg_url
    )

    actual = stars._from_database(
        latitude=47.61,  # round latitude to 2 decimal places
        longitude=-122.33,  # round longitude to 2 decimal places
        queried_date_utc="2019-12-09",
        database_url=test_database.pg_url,
    )
    assert actual == parsed_star_visbility_forecast
