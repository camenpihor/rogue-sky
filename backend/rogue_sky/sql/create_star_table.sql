DROP TABLE IF EXISTS daily_star_visibility_forecast;

CREATE TABLE daily_star_visibility_forecast (
    latitude NUMERIC,
    longitude NUMERIC,
    queried_date_utc DATE,
    weather_date_utc DATE,
    prediction NUMERIC,
    PRIMARY KEY (latitude, longitude, queried_date_utc, weather_date_utc)
)
;
