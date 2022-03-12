"""Get 8-day weather forecasts from DarkSky.

Includes methods to get weather from DarkSky and repackaging for sending via JSON.

The main entry-point is the `get_weather_forecast` method which retrieves the weather
forecast at aprovided lat-lon coordinate, and repackages it for sending via JSON.

DarkSky API docs: https://darksky.net/dev/docs
"""
import json
import logging

import arrow
import geopy
import requests

DARKSKY_URL = "https://api.darksky.net/forecast/{api_key}/{latitude},{longitude}"

# {serialized_column: darksky_column}
DAILY_WEATHER_MAPPING = {
    "weather_date_local": "time",
    "sunrise_time_local": "sunriseTime",
    "sunset_time_local": "sunsetTime",
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
    "temperature_max_f": "temperatureMax",
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
        raise requests.exceptions.HTTPError(  # pylint: disable=raise-missing-from
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
                weather_date_local: "2019-01-01",
                weather_json: JSON({
                    ...
                })
            },
            ...
        ]
    """
    latitude = response_json["latitude"]
    longitude = response_json["longitude"]
    timezone = response_json["timezone"]

    def parse_local_unix_date(local_date):
        return arrow.get(local_date).strftime(DATE_FORMAT)

    def parse(data, key):
        value = data.get(key, None)
        if value is not None:
            if key == "time":
                # `time` is returned by DarkSky in time local to the weather requested
                return parse_local_unix_date(local_date=value)
            # these times are returned by DarkSky in UTC
            if key in ("sunriseTime", "sunsetTime"):
                return arrow.get(value).to(timezone).format("h:mm a ZZZ")
        return value

    return [
        {
            "latitude": latitude,
            "longitude": longitude,
            "queried_date_utc": queried_date_utc,
            "timezone": timezone,
            "weather_date_local": parse_local_unix_date(local_date=daily_weather["time"]),
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
            "exclude": [
                "alerts",
                "flags",
                "hourly",
                "minutely",
                "offset",
                "currently",
            ]
        },
    )
    return _parse_darksky_response(response_json=response.json(), queried_date_utc=queried_date_utc)


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
        "timezone": response[0]["timezone"],
        "daily_forecast": [json.loads(daily_weather["weather_json"]) for daily_weather in response],
    }


def get_weather_forecast(latitude, longitude, api_key):
    """Get the 8-day weather forecast from the DarkSky API.

    Parameters
    ----------
    latitude : float
        Latitude at which to get weather.
    longitude : float
        Longitude at when to get weather.
    api_key : str
        DarkSky secret developer key.

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
    response = _from_darksky(
        latitude=latitude,
        longitude=longitude,
        queried_date_utc=queried_date_utc,
        api_key=api_key,
    )
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
    raise ValueError(f"Could not parse {address}")
