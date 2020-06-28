"""Get 8-day star visibility forecasts using weather data.

The main use-case class is the `get_star_forecast` method which retrieves the star
visiblity forecast at aprovided lat-lon coordinate, and repackages it for sending via
JSON.
"""
import logging

import arrow
import geopy
import numpy as np

from . import darksky, moon

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


def _from_weather(weather_forecast):
    """Get today's 8-day star visibility forecast from weather.

    Parameters
    ----------
    weather_forecast : dict
        {
            "latitude": 47.6062,
            "longitude": -122.3321,
            "queried_date_utc": "2019-11-15",
            "timezone": "America/New_York",
            "daily_forecast": [{daily_weather}]
        }

    Returns
    -------
    list(dict)
        [
            {
                latitude: 42.3601,
                longitude: -71.0589,
                queried_date_utc: "2019-01-01",
                weather_date_local: "2019-01-01",
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
            "weather_date_local": daily_weather["weather_date_local"],
            "prediction": np.round(star_visibility, 2),
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
                weather_date_local: "2019-01-01",
                prediction: 0.7,
            },
            ...
        ]
    weather_forecast : dict(dict)
        {
            "latitude": 47.6062,
            "longitude": -122.3321,
            "queried_date_utc": "2019-11-15",
            "timezone": "America/New_York",
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
            "timezone": "America/New_York",
            "daily_forecast": {
                [
                    <weather info>,
                    "star_visibility": 0.7
                ],
                ...
            },
        }
    """
    _logger.info(
        "(%s, %s, %s): Serializing to API output...",
        predictions[0]["latitude"],
        predictions[0]["longitude"],
        predictions[0]["queried_date_utc"],
    )
    star_forecast = weather_forecast.copy()

    locator = geopy.geocoders.Nominatim(user_agent="rogue_sky", timeout=3)
    location = locator.reverse(
        f"{star_forecast['latitude']}, {star_forecast['longitude']}"
    ).raw

    if "city" in location["address"]:
        star_forecast["city"] = location["address"]["city"]
    else:
        star_forecast["city"] = location["address"]["town"]
    star_forecast["state"] = location["address"].get("state", None)

    zipped = zip(star_forecast["daily_forecast"], predictions)
    for day_forecast, star_visibility in zipped:
        moon_rise_time = moon.get_rise_time(
            local_date=arrow.get(day_forecast["weather_date_local"])
            .replace(tzinfo=star_forecast["timezone"])
            .datetime,
            latitude=star_forecast["latitude"],
            longitude=star_forecast["longitude"],
        )

        day_forecast["moonrise_time_local"] = (
            arrow.get(moon_rise_time).format("h:mm a ZZZ")
            if moon_rise_time
            else moon_rise_time
        )
        day_forecast["moon_illumination"] = moon.phase_to_illumination(
            phase=day_forecast["moon_phase_pct"]
        )
        day_forecast["star_visibility"] = star_visibility["prediction"]

    return star_forecast


def get_star_forecast(latitude, longitude, api_key):
    """Get the 8-day weather forecast from cache, or the DarkSky API.

    Parameters
    ----------
    latitude : float
        Latitude at which to get weather.
    longitude : float
        Longitude at when to get weather.

    Returns
    -------
    dict
        {
            "latitude": 42.3601,
            "longitude": -71.0589,
            "city": "Seattle",
            "state": "Washington",
            "queried_date_utc": "2019-01-01",
            "timezone": "America/New_York",
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
    weather_forecast = darksky.get_weather_forecast(
        latitude=latitude, longitude=longitude, api_key=api_key,
    )
    predictions = _from_weather(weather_forecast=weather_forecast)
    return _serialize(predictions=predictions, weather_forecast=weather_forecast)
