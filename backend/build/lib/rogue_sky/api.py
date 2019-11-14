"""Flask application for the backend API."""
import logging
import os

from flask import Flask
from flask_cors import CORS

from . import darksky

app = Flask(__name__)  # pylint: disable=invalid-name
CORS(app)

app.config.from_object("rogue_sky.config.DevelopmentConfig")
logging.basicConfig(level=logging.INFO)


@app.route("/")
def ping_test():
    """Backend API ping test."""
    return "Success"


@app.route("/weather/<latitude>,<longitude>")
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
