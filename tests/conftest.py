import contextlib
import json
import os

import pkg_resources
import psycopg2
from psycopg2 import sql
import pytest

PG_URL = os.environ["TEST_DATABASE_URL"]


class TestDatabase:
    pg_url = PG_URL

    def __init__(self):
        self.tear_down()

    @contextlib.contextmanager
    def get_cursor(self):
        connection = psycopg2.connect(self.pg_url)
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            connection.commit()
            cursor.close()
            connection.close()

    def tear_down(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                """
            SELECT schemaname, tablename FROM pg_catalog.pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ;
            """
            )
            tables = cursor.fetchall()
            print("Cleaning test database")
            for (schema, table) in tables:
                cursor.execute(
                    sql.SQL("DROP TABLE {}").format(sql.Identifier(schema, table))
                )


@pytest.fixture(scope="function")
def test_database():
    database = TestDatabase()
    yield database
    database.tear_down()


@pytest.fixture(scope="function")
def darksky_json_response():
    """Response from DarkSky that was translated to JSON."""
    return json.loads(
        pkg_resources.resource_string("tests.resources", "test_darksky_response.json")
    )


@pytest.fixture(scope="function")
def parsed_darksky_forecast():
    """A parsed DarkSky forecast.

    Parsed with rogue_sky.backend.darksky._parse_darksky_response()
    """
    return json.loads(
        pkg_resources.resource_string(
            "tests.resources", "test_parsed_darksky_forecast.json"
        )
    )


@pytest.fixture(scope="function")
def serialized_weather_forecast():
    """A serialized daily weather forecast.

    Serialized with rogue_sky.backend.darksky._serialize()
    """
    return json.loads(
        pkg_resources.resource_string(
            "tests.resources", "test_serialized_weather_forecast.json"
        )
    )


@pytest.fixture(scope="function")
def parsed_star_visbility_forecast():
    """A parsed star visibility forecast.

    Parsed with rogue_sky.backend.stars._from_weather()
    """
    return json.loads(
        pkg_resources.resource_string(
            "tests.resources", "test_parsed_star_visibility_forecast.json"
        )
    )
