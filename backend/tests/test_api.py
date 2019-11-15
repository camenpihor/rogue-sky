import json

from rogue_sky import darksky, postgres_utilities


def test_empty_db(backend_api_client):
    response = backend_api_client.get("/")
    assert response.status_code == 200


# pylint: disable=bad-continuation
def test_weather_forecast(
    requests_mock, backend_api_client, test_database, darksky_json_response
):
    latitude = 47.6062
    longitude = 122.3321
    api_key = backend_api_client.application.config["DARKSKY_API_KEY"]

    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    requests_mock.get(
        darksky.DARKSKY_URL.format(
            api_key=api_key, latitude=latitude, longitude=longitude
        ),
        json=darksky_json_response,
    )
    response = backend_api_client.get(f"api/weather/{latitude},{longitude}")
    assert response.status_code == 200

    actual = json.loads(response.data)
    assert len(actual) == 8
    assert set(actual["0"]["weather_json"].keys()) == set(
        darksky.DAILY_WEATHER_MAPPING.keys()
    )


def test_weather_forecast(
    requests_mock, backend_api_client, test_database, darksky_json_response
):
    latitude = 47.6062
    longitude = 122.3321
    api_key = backend_api_client.application.config["DARKSKY_API_KEY"]

    postgres_utilities.create_weather_table(pg_url=test_database.pg_url)
    postgres_utilities.create_star_table(pg_url=test_database.pg_url)
    requests_mock.get(
        darksky.DARKSKY_URL.format(
            api_key=api_key, latitude=latitude, longitude=longitude
        ),
        json=darksky_json_response,
    )
    response = backend_api_client.get(f"api/stars/{latitude},{longitude}")
    assert response.status_code == 200

    actual = json.loads(response.data)
    assert len(actual) == 8
    assert set(actual["0"].keys()) == set(
        ["latitude", "longitude", "weather_date_utc", "queried_date_utc", "prediction"]
    )
