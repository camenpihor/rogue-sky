"""Get 8-day star visibility forecasts using weather data.

The main use-case class is the `get_star_forecast` method which retrieves the star
visiblity forecast at aprovided lat-lon coordinate, and repackages it for sending via
JSON.
"""
import logging

import arrow
import geopy
import numpy as np

from . import darksky, postgres_utilities

DATE_FORMAT = "%Y-%m-%d"

_logger = logging.getLogger(__name__)


def predict_visibility(cloud_cover):
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


def _from_database(latitude, longitude, queried_date_utc, database_url):
    """Get the star visibility forecast from the local database, if exists.

    Check the local database for predictions at the provided lat-lon coordinates that was
    retrieved today (queried_date_utc is today). If the visibility forecast for today
    has not already been retrieved, return None.

    Parameters
    ----------
    latitude : float
        Latitude at which to get predictions.
    longitude : float
        Longitude at when to get predictions.
    queried_date_utc : str
        The query date (today) in UTC. This is created at initialization time.
    database_url : str
        Connection url to a postgres database.

    Returns
    -------
    list(dict)
        Should return the same type signature as `_from_weather()`.
        [
            {
                latitude: 42.3601,
                longitude: -71.0589,
                queried_date_utc: "2019-01-01",
                weather_date_utc: "2019-01-01",
                prediction: 0.7,
            },
            ...
        ]
    """
    _logger.info(
        "(%s, %s, %s): Checking database...", latitude, longitude, queried_date_utc,
    )
    result = postgres_utilities.batch_from_postgres(
        latitude=latitude,
        longitude=longitude,
        queried_date_utc=queried_date_utc,
        table_name="daily_star_visibility_forecast",
        pg_url=database_url,
    )

    def date_to_string(date):
        return date.strftime(DATE_FORMAT)

    def decimal_to_float(decimal):
        return float(decimal)

    from_database = [
        {
            "latitude": decimal_to_float(decimal=daily_weather["latitude"]),
            "longitude": decimal_to_float(decimal=daily_weather["longitude"]),
            "queried_date_utc": date_to_string(date=daily_weather["queried_date_utc"]),
            "weather_date_utc": date_to_string(date=daily_weather["weather_date_utc"]),
            "prediction": decimal_to_float(decimal=daily_weather["prediction"]),
        }
        for daily_weather in result
    ]
    if from_database:  # list is not empty
        _logger.info(
            "(%s, %s, %s): Found in database!", latitude, longitude, queried_date_utc
        )
    else:
        _logger.info(
            "(%s, %s, %s): Not found in database...",
            latitude,
            longitude,
            queried_date_utc,
        )
    return from_database


def _to_database(predictions, database_url):
    """Persist the star visibilty forecast to the database at database_url.

    Parameters
    ----------
    predictions : list(dict)
        Each dict in the list is the star visibility prediction for a day. The keys of the
        dictionary should match the columns of the `daily_star_visibility_forecast` table
        in the database.
    database_url : str
        Connection url to a postgres database.
    """
    _logger.info(
        "(%s, %s, %s): Persisting to database...",
        predictions[0]["latitude"],
        predictions[0]["longitude"],
        predictions[0]["queried_date_utc"],
    )
    postgres_utilities.batch_to_postgres(
        batch=predictions,
        pg_url=database_url,
        table_name="daily_star_visibility_forecast",
    )


def _from_weather(weather_forecast):
    """Get today's 8-day star visibility forecast from weather.

    Parameters
    ----------
    weather_forecast : dict
        {
            "latitude": 47.6062,
            "longitude": -122.3321,
            "queried_date_utc": "2019-11-15",
            "daily_forecast": [{daily_weather}]
        }

    Returns
    -------
    list(dict)
        Should return the same type signature as `_from_database()`.
        [
            {
                latitude: 42.3601,
                longitude: -71.0589,
                queried_date_utc: "2019-01-01",
                weather_date_utc: "2019-01-01",
                prediction: 0.7,
            },
            ...
        ]
    """
    cloud_cover = np.array(
        [
            daily_weather["cloud_cover_pct"]
            for daily_weather in weather_forecast["daily_forecast"]
        ]
    )
    return [
        {
            "latitude": weather_forecast["latitude"],
            "longitude": weather_forecast["longitude"],
            "queried_date_utc": weather_forecast["queried_date_utc"],
            "weather_date_utc": daily_weather["weather_date_utc"],
            "prediction": star_visibility,
        }
        for daily_weather, star_visibility in zip(
            weather_forecast["daily_forecast"],
            predict_visibility(cloud_cover=cloud_cover),
        )
    ]


def _serialize(predictions, weather_forecast):
    """Serialize the star visibility and weather forecast into valid JSON.

    Parameters
    ----------
    predictions : list(dict)
        Each dict in the list contains the prediction for a day.
        [
            {
                latitude: 42.3601,
                longitude: -71.0589,
                queried_date_utc: "2019-01-01",
                weather_date_utc: "2019-01-01",
                prediction: 0.7,
            },
            ...
        ]
    weather_forecast : dict(dict)
        {
            "latitude": 47.6062,
            "longitude": -122.3321,
            "queried_date_utc": "2019-11-15",
            "daily_forecast": [{daily_weather}]
        }

    Returns
    -------
    dict(dict)
        JSON-parseable nested dictionary containing the 8-day daily weather
        forecast.
        {
            "latitude": 42.3601,
            "longitude": -71.0589,
            "city": "Seattle",
            "state": "Washington",
            "queried_date_utc": "2019-01-01",
            "daily_forecast": {
                [
                    <weather info>,
                    "star_visibility": 0.7
                ],
                ...
            },
        }
    """
    star_forecast = weather_forecast.copy()
    _logger.info(
        "(%s, %s, %s): Serializing to API output...",
        predictions[0]["latitude"],
        predictions[0]["longitude"],
        predictions[0]["queried_date_utc"],
    )
    locator = geopy.geocoders.Nominatim(user_agent="rogue_sky")
    location = locator.reverse(
        f"{star_forecast['latitude']}, {star_forecast['longitude']}"
    ).raw

    star_forecast["city"] = location["address"]["city"]
    star_forecast["state"] = location["address"]["state"]

    zipped = zip(star_forecast["daily_forecast"], predictions)
    for day_forecast, star_visibility in zipped:
        day_forecast["star_visibility"] = star_visibility["prediction"]

    return star_forecast


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
    dict
        {
            "latitude": 42.3601,
            "longitude": -71.0589,
            "city": "Seattle",
            "state": "Washington",
            "queried_date_utc": "2019-01-01",
            "daily_forecast": {
                [
                    <weather info>,
                    "star_visibility": 0.7
                ],
                ...
            },
        }
    """
    queried_date_utc = arrow.get().strftime("%Y-%m-%d")
    _logger.info(
        "Getting daily star visibility forecast for (%s, %s) on %s",
        latitude,
        longitude,
        queried_date_utc,
    )
    predictions = _from_database(
        latitude=latitude,
        longitude=longitude,
        queried_date_utc=queried_date_utc,
        database_url=database_url,
    )
    if not predictions:  # list is empty
        weather_forecast = darksky.get_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            api_key=api_key,
            database_url=database_url,
        )
        predictions = _from_weather(weather_forecast=weather_forecast)
        _to_database(predictions=predictions, database_url=database_url)
    return _serialize(predictions=predictions, weather_forecast=weather_forecast)
