# pylint: disable=protected-access
# requests-mock package creates a pytest fixture, `requests_mock`
import json

import numpy as np
import pytest
import requests

from rogue_sky import darksky, postgres_utilities, stars

API_KEY = "TEST"
LATITUDE = 1.0
LONGITUDE = 2.0
TEST_URL = darksky.DARKSKY_URL.format(
    api_key=API_KEY, latitude=LATITUDE, longitude=LONGITUDE
)


def test_predict_visibility():
    actual = stars.predict_visibility(np.array([1, 0, np.nan]))
    np.testing.assert_array_equal(actual, np.array([0, 1, np.nan]))


def test_from_weather(requests_mock, serialized_weather_forecast):
    actual = stars._from_weather(weather_forecast=serialized_weather_forecast)
    assert isinstance(actual, list)
    assert isinstance(actual[0], dict)
    assert set(actual[0].keys()) == set(
        ["latitude", "longitude", "queried_date_utc", "weather_date_utc", "prediction"]
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


def test_serialize(parsed_star_visbility_forecast):
    actual = stars._serialize(predictions=parsed_star_visbility_forecast)
    assert isinstance(actual, dict)
    assert len(actual) == len(parsed_star_visbility_forecast)
    assert actual["0"]["prediction"] == parsed_star_visbility_forecast[0]["prediction"]


def test_get_star_forecast(requests_mock, test_database, darksky_json_response):
    requests_mock.get(TEST_URL, json=darksky_json_response)
    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    postgres_utilities.create_star_table(pg_url=test_database.pg_url)
    actual = stars.get_star_forecast(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        api_key=API_KEY,
        database_url=test_database.pg_url,
    )
    assert len(actual) == len(darksky_json_response["daily"]["data"])
    assert isinstance(actual, dict)
    assert isinstance(json.dumps(actual), str)  # is json-serializable


def test_from_database(test_database, parsed_star_visbility_forecast):
    postgres_utilities.create_star_table(pg_url=test_database.pg_url)
    stars._to_database(
        predictions=parsed_star_visbility_forecast, database_url=test_database.pg_url
    )

    actual = stars._from_database(
        latitude=47.6062,
        longitude=-122.3321,
        queried_date_utc="2019-11-14",
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
        queried_date_utc="2019-11-14",
        database_url=test_database.pg_url,
    )
    assert actual == parsed_star_visbility_forecast
