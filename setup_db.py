#!/usr/bin/env python
import os
import subprocess
from urllib.parse import urlparse

from rogue_sky import postgres_utilities

DATABASE_URL = os.environ["DATABASE_URL"]
TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]


def _create_db(database_url):
    parsed_url = urlparse(database_url)

    database_name = parsed_url.path[1:]  # strip the leading slash
    password = parsed_url.password
    username = parsed_url.username

    commands = [
        f"DROP ROLE IF EXISTS {username}",
        f"DROP DATABASE IF EXISTS {database_name}",
        f"CREATE DATABASE {database_name}",
        f"CREATE ROLE {username} LOGIN PASSWORD '{password}'",
        f"GRANT ALL PRIVILEGES ON DATABASE {database_name} TO {username}",
    ]

    for command in commands:
        subprocess.check_call(["psql", "postgres", "-c", command, "-e"])


def setup_db():
    print("Creating test database...")
    _create_db(database_url=TEST_DATABASE_URL)

    print("Creating production...")
    _create_db(database_url=DATABASE_URL)

    print("Creating weather table in production...")
    postgres_utilities.create_weather_table(pg_url=DATABASE_URL)
    postgres_utilities.create_star_table(pg_url=DATABASE_URL)

    print("Success.")


if __name__ == "__main__":
    setup_db()
