"""Flask application for the backend API."""
import logging

from flask import Flask
from flask_cors import CORS

from . import darksky, stars

app = Flask(__name__)  # pylint: disable=invalid-name
CORS(app, resources={"/api/*": {"origins": "http://localhost:8080"},})

app.config.from_object("rogue_sky.config.DevelopmentConfig")
logging.basicConfig(level=logging.INFO)


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


@app.route("/api/stars/<latitude>,<longitude>")
def star_visibility_forecast(latitude, longitude):
    """Get daily star visibility forecast for location."""
    latitude = float(latitude)
    longitude = float(longitude)
    return stars.get_star_forecast(
        latitude=latitude,
        longitude=longitude,
        api_key=app.config["DARKSKY_API_KEY"],
        database_url=app.config["DATABASE_URL"],
    )
