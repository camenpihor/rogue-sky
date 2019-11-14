"""Get 8-day star visibility forecasts using weather data.

The main use-case class is the `get_star_forecast` method which retrieves the star
visiblity forecast at aprovided lat-lon coordinate, and repackages it for sending via
JSON.
"""
import pkg_resources

import arrow

from . import darksky

VERSION = pkg_resources.get_distribution("rogue-sky").version


class StarVisibilityModel:
    """Really really naive model for right now."""

    def predict(self, cloud_cover):
        """Predict star visibility.

        Parameters
        ----------
        cloud_cover : np.ndarray
            The percentage of cloud cover in the sky.

        Returns
        -------
        np.ndarray(float)
            Each prediction is between 0 and 1, where 1 is great visibility and 0 is no
            visibility at all.
        """
        return 1 - cloud_cover


def _from_database():
    return


def _to_database():
    return


def _from_weather(weather_forecast):
    """Get today's 8-day star visibility forecast from weather.

    Parameters
    ----------
    weather_forecast : dict
        {
            0: {
                "latitude": 42.3601,
                "longitude": -71.0589,
                "queried_date_utc": "2019-01-01",
                "weather_date_utc": "2019-11-10",
                "weather_json": weather_json,
            },
            1: {
                "latitude": 42.3601,
                "longitude": -71.0589,
                "queried_date_utc": "2019-01-01",
                "weather_date_utc": "2019-11-11",
                "weather_json": weather_json,
            },
            ...
        }

    Returns
    -------
    list(dict)
        Should return the same type signature as `_from_database()`.
    """
    visibility_model = StarVisibilityModel()
    cloud_cover = np.array(
        [
            daily_weather["weather_json"].get("cloud_cover", None)
            for daily_weather in weather_forecast.values()
        ]
    )
    predictions = visibility_model.predict(cloud_cover=cloud_cover)
    return [
        {
            "latitude": daily_weather["latitude"],
            "longitude": daily_weather["longitude"],
            "queried_date_utc": daily_weather["queried_date_utc"],
            "weather_date_utc": daily_weather["weather_date_utc"],
            "star_visibility_prediction": star_visibility,
            "model_version": VERSION,
        }
        for daily_weather, star_visibility in zip(weather_forecast.values(), predictions)
    ]


def _serialize():
    return


def get_star_forecast(latitude, longitude, api_key, database_url):
    """Get the 8-day weather forecast from cache, or the DarkSky API.

    Parameters
    ----------
    latitude : float
        Latitude at which to get weather.
    longitude : float
        Longitude at when to get weather.
    database_url : str
        Connection url to a postgres database.

    Returns
    -------
    None
    """
    queried_date_utc = arrow.get().strftime("%Y-%m-%d")
    _logger.info(
        "Getting daily star visibility forecast for (%s, %s) on %s",
        latitude,
        longitude,
        queried_date_utc,
    )
    response = _from_database(
        latitude=latitude,
        longitude=longitude,
        queried_date_utc=queried_date_utc,
        version=VERSION,
        database_url=database_url,
    )
    if not response:  # list is empty
        weather_forecast = darksky.get_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            api_key=api_key,
            database_url=database_url,
        )
        response = _from_weather(weather_forecast=weather_forecast)
        _to_database(response=response, database_url=database_url)
    return _serialize(response=response)
