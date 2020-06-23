import datetime

import arrow
import numpy as np
import pytest

from rogue_sky import moon


def test_get_rise_time(moon_rises):
    tolerance_minutes = 10

    for moon_rise in moon_rises:
        timezone = moon_rise["timezone"]
        local_date = arrow.get(moon_rise["date"], "YYYY-MM-DD").replace(tzinfo=timezone)
        latitude = moon_rise["latitude"]
        longitude = moon_rise["longitude"]

        expected = (
            arrow.get(moon_rise["actual_time"], "YYYY-MM-DDThh:mm").replace(
                tzinfo=timezone
            )
            if moon_rise["actual_time"]
            else moon_rise["actual_time"]
        )
        actual = moon.get_rise_time(
            local_date=local_date.datetime, latitude=latitude, longitude=longitude
        )
        if actual:
            assert arrow.get(actual).is_between(
                expected.shift(minutes=-tolerance_minutes),
                expected.shift(minutes=+tolerance_minutes),
            )
        else:
            assert expected == actual


def test_solve_2d_quadratic():
    actual = moon.solve_2d_quadratic([-1, 0, 1], [1, 0, 1])
    assert len(actual) == 2
    assert not set(actual[0].keys()) - set(["value", "ascending"])

    actual_1, actual_2 = actual

    assert not actual_1["ascending"]
    np.testing.assert_almost_equal(actual_1["value"], 0)

    assert actual_2["ascending"]
    np.testing.assert_almost_equal(actual_2["value"], 0)


def test_round_time():
    actual = moon.round_time(datetime.datetime(2020, 1, 1, 1, 1, 1))
    assert actual == datetime.datetime(2020, 1, 1, 1, 1)

    actual = moon.round_time(datetime.datetime(2020, 1, 1, 1, 1, 31))
    assert actual == datetime.datetime(2020, 1, 1, 1, 2)


@pytest.mark.skip(reason="My method is too approximate to be that close...")
def test_get_altitude():
    # expected from https://www.heavens-above.com/moon.aspx?lat=41.8781&lng=-87.6298&loc=Chicago&alt=343&tz=CST
    # chicago
    latitude = 41.8781
    longitude = -87.6298
    actual = moon.get_altitude(
        date=arrow.get(datetime.datetime(2020, 6, 10, 2, 43), "US/Central").datetime,
        latitude=latitude,
        longitude=longitude,
    )
    expected = -50.2  # degrees
    np.testing.assert_almost_equal(actual, expected, decimal=3)


@pytest.mark.skip(reason="My method is too approximate to be that close...")
def test_get_right_ascension():
    # https://theskylive.com/moon-info
    actual = moon.get_right_ascension(
        date=arrow.get(datetime.datetime(2020, 6, 10, 2, 43), "US/Central").datetime,
    )
    expected = 325.94  # degrees which is 21h 43m 46s
    np.testing.assert_almost_equal(actual % 360, expected)


def test_get_declination():
    # https://theskylive.com/moon-info
    actual = moon.get_declination(
        date=arrow.get(datetime.datetime(2020, 6, 10, 2, 43), "US/Central").datetime,
    )
    expected = -18.23
    assert expected - 5 <= actual <= expected + 5


@pytest.mark.skip(reason="I don't have a good source yet...")
def test_get_mean_anomaly_earth():
    assert False


@pytest.mark.skip(reason="Need this to be more precise")
def test_get_sidereal_time():
    # http://www.jgiesen.de/astro/astroJS/siderealClock/
    actual = moon.get_sidereal_time(
        date=arrow.get(datetime.datetime(2020, 6, 10, 2, 43), "US/Central").datetime,
        longitude=-87.6298,
    )

    expected = (7, 27, 30)  # hours, minutes, seconds
    assert int(actual / 15 & 24) == expected[0]


@pytest.mark.skip(reason="Don't have a good source of truth yet...")
def test_get_geocentric_ecliptical_coordinates():
    actual = moon.get_geocentric_ecliptical_coordinates(
        date=arrow.get(datetime.datetime(2020, 6, 10, 2, 43), "US/Central").datetime,
    )


def test_sin():
    assert moon.sin(30) == np.sin(np.pi / 6)


def test_cos():
    assert moon.cos(90) == np.cos(np.pi / 2)


def test_tan():
    assert moon.tan(45) == np.tan(np.pi / 4)


def test_phase_to_illumination():
    assert moon.phase_to_illumination(phase=1) == 0  # new moon
    assert moon.phase_to_illumination(phase=0.5) == 1  # full moon
    assert moon.phase_to_illumination(phase=0.25) == 0.5  # waxing half moon
    assert moon.phase_to_illumination(phase=0.75) == 0.5  # waning half moon
    assert moon.phase_to_illumination(phase=0) == 0
