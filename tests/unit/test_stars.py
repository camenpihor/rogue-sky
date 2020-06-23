# pylint: disable=protected-access
# requests-mock package creates a pytest fixture, `requests_mock`
import numpy as np

from rogue_sky import stars


def test_predict_visibility():
    actual = stars.predict_visibility(np.array([1, 0, np.nan]))
    np.testing.assert_array_equal(actual, np.array([0, 1, np.nan]))


def test_from_weather(serialized_weather_forecast):
    actual = stars._from_weather(weather_forecast=serialized_weather_forecast)
    assert isinstance(actual, list)
    assert isinstance(actual[0], dict)
    assert set(actual[0].keys()) == set(
        ["latitude", "longitude", "queried_date_utc", "weather_date_local", "prediction"]
    )
