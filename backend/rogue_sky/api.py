"""Flask application for the backend API."""
import logging

from flask import Flask
from flask_cors import CORS
import geopy

from . import darksky, stars

app = Flask(__name__)  # pylint: disable=invalid-name
CORS(app, resources={"/api/*": {"origins": "http://localhost:8080"},})

app.config.from_object("rogue_sky.config.DevelopmentConfig")
logging.basicConfig(level=logging.INFO)


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
            geo_locator = geopy.geocoders.Nominatim(user_agent="rogue_sky")
            location = geo_locator.geocode(address)

            return location.latitude, location.longitude
    raise ValueError("Could not parse {address}")


@app.route("/")
def ping_test():
    """Backend API ping test."""
    return "Success"


@app.route("/api/weather/<latitude>,<longitude>")
def weather_forecast(latitude, longitude):
    """Get daily weather forecast for location."""
    latitude = float(latitude)
    longitude = float(longitude)
    return darksky.get_weather_forecast(
        latitude=latitude,
        longitude=longitude,
        api_key=app.config["DARKSKY_API_KEY"],
        database_url=app.config["DATABASE_URL"],
    )


@app.route("/api/stars/<address>")
def star_visibility_forecast(address):
    """Get daily star visibility forecast for location."""
    latitude, longitude = parse_address(address=address)
    return stars.get_star_forecast(
        latitude=latitude,
        longitude=longitude,
        api_key=app.config["DARKSKY_API_KEY"],
        database_url=app.config["DATABASE_URL"],
    )
