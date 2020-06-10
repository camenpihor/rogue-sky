import contextlib
import json
import os

import pkg_resources
import pytest


@pytest.fixture(scope="function")
def darksky_json_response():
    """Return a response from DarkSky that was translated to JSON."""
    return json.loads(
        pkg_resources.resource_string("tests.resources", "test_darksky_response.json")
    )


@pytest.fixture(scope="function")
def parsed_darksky_forecast():
    """Return a parsed DarkSky forecast.

    Parsed with rogue_sky.darksky._parse_darksky_response()
    """
    return json.loads(
        pkg_resources.resource_string(
            "tests.resources", "test_parsed_darksky_forecast.json"
        )
    )


@pytest.fixture(scope="function")
def serialized_weather_forecast():
    """Return a serialized daily weather forecast.

    Serialized with rogue_sky.darksky._serialize()
    """
    return json.loads(
        pkg_resources.resource_string(
            "tests.resources", "test_serialized_weather_forecast.json"
        )
    )


@pytest.fixture(scope="function")
def parsed_star_visbility_forecast():
    """Return a parsed star visibility forecast.

    Parsed with rogue_sky.stars._from_weather()
    """
    return json.loads(
        pkg_resources.resource_string(
            "tests.resources", "test_parsed_star_visibility_forecast.json"
        )
    )


@pytest.fixture(scope="function")
def moon_rises():
    """Return a set of actual moon rise times with locations and date."""
    return json.loads(
        pkg_resources.resource_string(
            "tests.resources", "test_moon_rise_times.json"
        )
    )
