"""Utilities for accessing the PostgreSQL database."""
from contextlib import contextmanager
import logging
import subprocess
from urllib.parse import urlparse

import pkg_resources
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import sqlparse

_logger = logging.getLogger(__name__)


@contextmanager
def connect(pg_url):
    """Create a context manager for psycopg2.connect().

    Commit changes and closes connection upon exit.

    Parameters
    ----------
    pg_url : str
        Database connection url.

    Yields
    ------
    psycopg2.extensions.connection
    """
    connection = psycopg2.connect(pg_url)
    try:
        yield connection
    finally:
        connection.commit()
        connection.close()


@contextmanager
def get_cursor(pg_url, **cursor_kwargs):
    """Create a context manager for psycopg2 cursor object.

    Commits changes, and closes the connection and cursor upon exit.

    Parameters
    ----------
    pg_url : str
        Database connection url.

    Yields
    ------
    psycopg2.extensions.cursor
    """
    with connect(pg_url) as connection:
        cursor = connection.cursor(**cursor_kwargs)
        try:
            yield cursor
        finally:
            cursor.close()


def execute_sql_file(pg_url, filename):
    """Execute the queries in a SQL file."""
    queries = pkg_resources.resource_string("rogue_sky.sql", filename)
    statements = sqlparse.split(queries, "utf-8")
    for statement in statements:
        # If the file ends with a semicolon, there will be a whitespace SQL statement
        # that we need to ignore
        if statement.strip():
            with get_cursor(pg_url) as cursor:
                cursor.execute(statement)


def create_weather_table(pg_url):
    """Create the weather table for DarkSky data."""
    execute_sql_file(pg_url, filename="create_weather_table.sql")


def create_star_table(pg_url):
    """Create the star visibility predictions table."""
    execute_sql_file(pg_url, filename="create_star_table.sql")


def batch_to_postgres(batch, pg_url, table_name):
    """Batch insert to data to PostgreSQL table.

    Parameters
    ----------
    batch : list(dict)
        Dictionaries must all be of the same form (same keys in the same order).
        Dictionary keys must match the columns names of the table at `table_name`.
    pg_url : str
        Database connection url.
    table_name : str
    """
    insert_query = to_insert_query(data=batch[0], table_name=table_name)

    with get_cursor(pg_url) as cursor:
        for data_dict in batch:
            cursor.execute(insert_query, tuple(data_dict.values()))


def to_insert_query(data, table_name):
    """Transform dictionary to PostgreSQL INSERT query.

    Parameters
    ----------
    data : dict
    table_name : str

    Returns
    -------
    psycopg2.sql.Composed
        INSERT query.
    """
    return sql.SQL("INSERT INTO {table} ({columns}) VALUES ({placeholders})").format(
        table=sql.Identifier(table_name),
        columns=sql.SQL(", ").join(map(sql.Identifier, data.keys())),
        placeholders=sql.SQL(", ").join(sql.Placeholder() * len(data)),
    )


def to_select_query(latitude, longitude, queried_date_utc, table_name):
    """Build PostgreSQL SELECT query.

    Find forecast matching the lat-lon coordinates to 1 decimal place, which is close
    enough in my opinion https://en.wikipedia.org/wiki/Decimal_degrees.

    Parameters
    ----------
    latitude : float
    longitude : float
    queried_date_utc : str
        YYYY-MM-DD.
    table_name : str

    Returns
    -------
    psycopg2.sql.Composed
        SELECT query.
    """
    query = """
    SELECT
        *
    FROM {table}

    WHERE
        ROUND(latitude, 1) = {latitude} AND
        ROUND(longitude, 1) = {longitude} AND
        queried_date_utc = {queried_date_utc}
    """
    return sql.SQL(query).format(
        table=sql.Identifier(table_name),
        latitude=sql.Literal(round(latitude, 1)),
        longitude=sql.Literal(round(longitude, 1)),
        queried_date_utc=sql.Literal(queried_date_utc),
    )


def batch_from_postgres(latitude, longitude, queried_date_utc, table_name, pg_url):
    """Select data in batch from PostgreSQL table.

    Uses a DictCursor, so that one can access the cursor response like a dictionary whose
    keys are the columns names.

    Parameters
    ----------
    latitude : float
    longitude : float
    queried_date_utc : str
        YYYY-MM-DD
    table_name : str
    pg_url : str
        Database connection url.

    Returns
    -------
    list(dict)
        List of all rows returned where each row is a dictionary of column_name: value.
    """
    select_query = to_select_query(
        latitude=latitude,
        longitude=longitude,
        queried_date_utc=queried_date_utc,
        table_name=table_name,
    )

    with get_cursor(pg_url, cursor_factory=RealDictCursor) as cursor:
        cursor.execute(select_query)
        return cursor.fetchall()


def _create_db(database_url):
    parsed_url = urlparse(database_url)

    database_name = parsed_url.path[1:]  # strip the leading slash
    password = parsed_url.password
    username = parsed_url.username

    commands = [
        f"DROP DATABASE IF EXISTS {database_name}",
        f"DROP ROLE IF EXISTS {username}",
        f"CREATE DATABASE {database_name}",
        f"CREATE ROLE {username} LOGIN PASSWORD '{password}'",
        f"GRANT ALL PRIVILEGES ON DATABASE {database_name} TO {username}",
    ]

    for command in commands:
        subprocess.check_call(["psql", "postgres", "-c", command, "-e"])


def setup_db(test_database_url, database_url):
    """Set up the test and production databases.

    test:
        1. create role
        2. create database

    production:
        1. create role
        2. create database
        3. create tables
    """
    _logger.info("Creating test database...")
    _create_db(database_url=test_database_url)

    _logger.info("Creating production...")
    _create_db(database_url=database_url)

    _logger.info("Creating weather table in production...")
    create_weather_table(pg_url=database_url)
    create_star_table(pg_url=database_url)

    _logger.info("Success.")
