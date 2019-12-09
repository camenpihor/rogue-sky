import datetime

from rogue_sky import postgres_utilities


def test_create_weather_table(test_database):
    postgres_utilities.create_weather_table(test_database.pg_url)
    with test_database.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_weather_forecast'
            """
        )
        actual_columns = [x for x, in cursor.fetchall()]

    expected_columns = [
        "latitude",
        "longitude",
        "queried_date_utc",
        "weather_date_local",
        "weather_json",
    ]
    assert set(actual_columns) == set(expected_columns)


def test_create_star_table(test_database):
    postgres_utilities.create_star_table(test_database.pg_url)
    with test_database.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_star_visibility_forecast'
            """
        )
        actual_columns = [x for x, in cursor.fetchall()]

    expected_columns = [
        "latitude",
        "longitude",
        "queried_date_utc",
        "weather_date_local",
        "prediction",
    ]
    assert set(actual_columns) == set(expected_columns)


def test_batch_to_postgres(test_database):
    with postgres_utilities.get_cursor(test_database.pg_url) as cursor:
        cursor.execute("CREATE TABLE testing (test INT);")

    postgres_utilities.batch_to_postgres(
        batch=[{"test": 1}], pg_url=test_database.pg_url, table_name="testing"
    )

    with postgres_utilities.get_cursor(test_database.pg_url) as cursor:
        cursor.execute("SELECT * FROM testing")
        actual = cursor.fetchone()
        assert actual == (1,)


def test_batch_from_postgres(test_database):
    with postgres_utilities.get_cursor(test_database.pg_url) as cursor:
        cursor.execute(
            """
            CREATE TABLE testing (
                latitude NUMERIC,
                longitude NUMERIC,
                queried_date_utc DATE
            );
            """
        )
        cursor.execute("INSERT INTO testing VALUES (1.0, 1.0, '2019-01-01');")

    actual = postgres_utilities.batch_from_postgres(
        latitude=1.0,
        longitude=1.0,
        queried_date_utc="2019-01-01",
        table_name="testing",
        pg_url=test_database.pg_url,
    )

    assert len(actual) == 1

    actual = actual[0]
    assert actual["latitude"] == 1.0
    assert actual["longitude"] == 1.0
    assert actual["queried_date_utc"] == datetime.date(2019, 1, 1)
