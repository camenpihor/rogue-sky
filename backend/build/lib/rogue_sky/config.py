"""Default configuration file for the backend API."""
# pylint: disable=too-few-public-methods
import os


class DevelopmentConfig:
    """Basic configuration for the backed API Flask application.

    Used for development.
    """

    TESTING = False
    DARKSKY_API_KEY = os.environ["DARKSKY_SECRET_KEY"]
    DATABASE_URL = os.environ["DATABASE_URL"]
    DEBUG = True


class TestingConfig(Config):
    """Configuration for testing the backed API Flask application."""

    FLASK_ENV = "development"
    TESTING = True
    DEBUG = True
    DATABASE_URL = os.environ["TEST_DATABASE_URL"]
    DARKSKY_API_KEY = "test_api_key"
