"""Get 8-day weather forecasts from DarkSky.

Includes methods to get weather from DarkSky, persist/retrieve data to/from a local
database, and repackage it for sending via JSON.

The main use-case class is the `get_weather_forecast` method which retrieves the weather
forecast at aprovided lat-lon coordinate, and repackages it for sending via JSON.

DarkSky API docs: https://darksky.net/dev/docs
"""
import json
import logging

import arrow
import geopy
import requests

from . import postgres_utilities


DARKSKY_URL = "https://api.darksky.net/forecast/{api_key}/{latitude},{longitude}"

# {database_column: darksky_column}
DAILY_WEATHER_MAPPING = {
    "weather_date_utc": "time",
    "sunrise_time_utc": "sunriseTime",
    "sunset_time_utc": "sunsetTime",
    "moon_phase_pct": "moonPhase",
    "precip_intensity_avg_in_hr": "precipIntensity",
    "precip_intensity_max_in_hr": "precipIntensityMax",
    "precip_probability": "precipProbability",
    "precip_type": "precipType",
    "dew_point_f": "dewPoint",
    "humidity_pct": "humidity",
    "pressure": "pressure",
    "wind_speed_mph": "windSpeed",
    "wind_gust_mph": "windGust",
    "cloud_cover_pct": "cloudCover",
    "uv_index": "uvIndex",
    "visibility_mi": "visibility",
    "ozone": "ozone",
    "temperature_min_f": "temperatureMin",
    "temperature_min_time_utc": "temperatureMinTime",
    "temperature_max_f": "temperatureMax",
    "temperature_max_time_utc": "temperatureMaxTime",
    "icon": "icon",
    "summary": "summary",
}
DATE_FORMAT = "%Y-%m-%d"

_logger = logging.getLogger(__name__)


def _make_request(api_key, latitude, longitude, queried_date_utc, **query_parameters):
    """Send request to the DarkSky API, and make sure it succeeds.

    Parameters
    ----------
    api_key : str
    latitude : float
    longitude : float
    queried_date_utc : str
        YYYY-MM-DD. Date of the query (today). Only used for logging.

    Returns
    -------
    requests.Response
    """
    url = DARKSKY_URL.format(api_key=api_key, latitude=latitude, longitude=longitude)
    _logger.info(
        "(%s, %s, %s): Requesting from DarkSky with parameters %s",
        latitude,
        longitude,
        queried_date_utc,
        query_parameters,
    )
    try:
        response = requests.get(url, query_parameters)
        response.raise_for_status()  # raise exception for non-success error codes
    except requests.exceptions.HTTPError:
        # we wrap HTTPError so that we don't print out the secret API key
        raise requests.exceptions.HTTPError(
            f"{response.status_code}: request failed for reason: {response.reason}"
        )
    return response


def _parse_darksky_response(response_json, queried_date_utc):
    """Parse JSON returned by DarkSky's API.

    Parameters
    ----------
    response_json : dict
        JSON received from DarkSky's API.
    queried_date_utc : str
        The date the query was performed (today) in YYYY-MM-DD format.

    Returns
    -------
    list(dict)
        [
            {
                latitude: 42.3601,
                longitude: -71.0589,
                queried_date_utc: "2019-01-01",
                weather_date_utc: "2019-01-01",
                weather_json: JSON({
                    ...
                })
            },
            ...
        ]
    """
    latitude = response_json["latitude"]
    longitude = response_json["longitude"]

    def parse_local_unix_date(local_date):
        return arrow.get(local_date).to(response_json["timezone"]).strftime(DATE_FORMAT)

    def parse(data, key):
        value = data.get(key, None)
        if value is not None:
            if key == "time":
                # `time` is returned by DarkSky in time local to the weather requested
                return parse_local_unix_date(local_date=value)
            # these times are returned by DarkSky in UTC
            # pylint: disable=bad-continuation
            if key in [
                "sunriseTime",
                "sunsetTime",
                "temperatureMinTime",
                "temperatureMaxTime",
            ]:
                return arrow.get(value).isoformat()
        return value

    return [
        {
            "latitude": latitude,
            "longitude": longitude,
            "queried_date_utc": queried_date_utc,
            "weather_date_utc": parse_local_unix_date(local_date=daily_weather["time"]),
            "weather_json": json.dumps(
                {
                    db_column: parse(data=daily_weather, key=darksky_key)
                    for db_column, darksky_key in DAILY_WEATHER_MAPPING.items()
                },
                sort_keys=True,
            ),
        }
        for daily_weather in response_json["daily"]["data"]
    ]


def _from_database(latitude, longitude, queried_date_utc, database_url):
    """Get the weather forecast from the local database, if exists.

    Check the local database for weather at the provided lat-lon coordinates that was
    retrieved today (queried_date_utc is today). If the weather forecast for today
    has not already been retrieved, return None.

    Parameters
    ----------
    latitude : float
        Latitude at which to get weather.
    longitude : float
        Longitude at when to get weather.
    queried_date_utc : str
        The query date (today) in UTC. This is created at initialization time.
    database_url : str
        Connection url to a postgres database.

    Returns
    -------
    list(dict)
        Should return the same type signature as `_from_darksky()`.
        [
            {
                latitude: 42.3601,
                longitude: -71.0589,
                queried_date_utc: "2019-01-01",
                weather_date_utc: "2019-01-01",
                weather_json: JSON({
                    ...
                })
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
        table_name="daily_weather_forecast",
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
            "weather_json": json.dumps(daily_weather["weather_json"], sort_keys=True),
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


def _from_darksky(latitude, longitude, queried_date_utc, api_key):
    """Get today's 8-day weather forecast from DarkSky.

    Parameters
    ----------
    latitude : float
        Latitude at which to get weather.
    longitude : float
        Longitude at when to get weather.
    queried_date_utc : str
        The query date (today) in UTC. This is created at initialization time.
    api_key : str
        DarkSky secret developer key.

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
                weather_json: JSON({
                    ...
                })
            },
            ...
        ]
    """
    response = _make_request(
        api_key=api_key,
        latitude=latitude,
        longitude=longitude,
        queried_date_utc=queried_date_utc,
        query_parameters={
            "exclude": ["alerts", "flags", "hourly", "minutely", "offset", "currently",]
        },
    )
    return _parse_darksky_response(
        response_json=response.json(), queried_date_utc=queried_date_utc
    )


def _to_database(response, database_url):
    """Persist the weather forecast to the database at database_url.

    Parameters
    ----------
    response : list(dict)
        Each dict in the list is the weather prediction for a day. The keys of the
        dictionary should match the columns of the `daily_weather_forecast` table in the
        database.
    database_url : str
        Connection url to a postgres database.
    """
    _logger.info(
        "(%s, %s, %s): Persisting to database...",
        response[0]["latitude"],
        response[0]["longitude"],
        response[0]["queried_date_utc"],
    )
    postgres_utilities.batch_to_postgres(
        batch=response, pg_url=database_url, table_name="daily_weather_forecast"
    )


def _serialize(response):
    """Serialize the weather forecast into a JSON-parseable nested dictionary.

    Parameters
    ----------
    response : list(dict)
        Each dict in the list contains the weather for a day.

    Returns
    -------
    dict(dict)
        JSON-parseable nested dictionary containing the 8-day daily weather
        forecast.
        {
            "latitude": 47.6062,
            "longitude": -122.3321,
            "queried_date_utc": "2019-11-15",
            "daily_forecast": [{daily_weather}]
        }
    """
    _logger.info(
        "(%s, %s, %s): Serializing to API output...",
        response[0]["latitude"],
        response[0]["longitude"],
        response[0]["queried_date_utc"],
    )

    return {
        "latitude": response[0]["latitude"],
        "longitude": response[0]["longitude"],
        "queried_date_utc": response[0]["queried_date_utc"],
        "daily_forecast": [
            json.loads(daily_weather["weather_json"]) for daily_weather in response
        ],
    }


def get_weather_forecast(latitude, longitude, api_key, database_url):
    """Get the 8-day weather forecast from cache, or the DarkSky API.

    Parameters
    ----------
    latitude : float
        Latitude at which to get weather.
    longitude : float
        Longitude at when to get weather.
    api_key : str
        DarkSky secret developer key.
    database_url : str
        Connection url to a postgres database.

    Returns
    -------
    dict(dict)
        JSON-parseable nested dictionary containing the 8-day daily weather
        forecast.
        {
            "latitude": 47.6062,
            "longitude": -122.3321,
            "queried_date_utc": "2019-11-15",
            "daily_forecast": [{daily_weather}]
        }
    """
    queried_date_utc = arrow.get().strftime("%Y-%m-%d")
    _logger.info(
        "Getting daily weather forecast for (%s, %s) on %s",
        latitude,
        longitude,
        queried_date_utc,
    )
    response = _from_database(
        latitude=latitude,
        longitude=longitude,
        queried_date_utc=queried_date_utc,
        database_url=database_url,
    )
    if not response:  # list is empty
        response = _from_darksky(
            latitude=latitude,
            longitude=longitude,
            queried_date_utc=queried_date_utc,
            api_key=api_key,
        )
        _to_database(response=response, database_url=database_url)
    return _serialize(response=response)


def parse_address(address):
    """Parse the adderss into coordinates.

    Parameters
    ----------
    address : str

    Returns
    -------
    tuple
        `(latitude, longitude)`
    """
    if address and address != "null":
        try:
            latitude, longitude = map(float, address.split(","))
            return latitude, longitude
        except ValueError:
            geo_locator = geopy.geocoders.Nominatim(user_agent="rogue_sky", timeout=3)
            location = geo_locator.geocode(address)

            return location.latitude, location.longitude
    raise ValueError("Could not parse {address}")
