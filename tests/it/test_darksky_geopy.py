import numpy as np

from rogue_sky import darksky


def test_parse_address():
    latitude, longitude = (47.6062, -122.3321)
    actual = darksky.parse_address(f"{latitude}, {longitude}")
    assert actual == (latitude, longitude)

    actual = darksky.parse_address(f"{latitude},{longitude}")
    assert actual == (latitude, longitude)

    actual = darksky.parse_address("Seattle, WA")
    np.testing.assert_array_almost_equal(actual, (latitude, longitude), decimal=2)
