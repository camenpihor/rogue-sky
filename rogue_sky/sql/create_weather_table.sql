DROP TABLE IF EXISTS daily_weather_forecast;

CREATE TABLE daily_weather_forecast (
    latitude NUMERIC,
    longitude NUMERIC,
    queried_date_utc DATE,
    weather_date_local DATE,
    weather_json JSONB,
    PRIMARY KEY (latitude, longitude, queried_date_utc, weather_date_local)
)
;
