# RogueSky

This repository has high hopes of having the following functionality:

1. Get forecasts from DarkSky
2. Forecast the star visibility anywhere in the continental US
3. An API to access these observations and predictions
4. A frontend for a website that hosts these observations and predictions

## What does star visibility entail

- cloud cover
  - any cloud cover is bad
- transparency
  - a measure of the amount of water vapor
  - essentially just humidity
  - how much water vapor is bad?
- seeing
  - a measure of the turbulence in the atmosphere
  - we can leave this for an advanced feature, the difference between a night of low atmospheric turbulence and high is the difference of how many rings of Jupiter one can see
  - I don't really know ways that we can get at this
  - https://weather.gc.ca/astro/seeing_e.html
- darkness
  - a measure of the darkness of the sky based on time of day and moon conditions
  - should get sunset/sunrise time
    - can be calculated https://en.wikipedia.org/wiki/Sunrise_equation#Complete_calculation_on_Earth
  - should get moon phase and position (learn more about what affects brightness of the moon)
    - moon phase can be calculated https://en.wikipedia.org/wiki/Lunar_phase#Calculating_phase
    - I think we can just use phase for now, and say that its darker when moon is less full

## Extra weather features that may be nice

- temperature
- wind speed
- precipitation

## Data

- NOAA forecast API https://api.weather.gov/gridpoints/TOP/31,80
  - like a week into the future
  - temperature
  - wind speed
  - humidity
  - precipitation
- DarkSky forecast and current https://darksky.net/dev/docs
  - first 1000 calls per day free and after its $0.0001 per call
  - temperature
  - humidity
  - cloud cover
  - precipitation
  - wind speed
  - sunrise/set time
  - moonphase
  - to build a historical database we can count how many calls we've made at the end of each day and then call 1000 minus that many historical queries
  - minute-by-minute for the next hour
  - hour-by-hour for the next 2 days
  - day-by-day for the next week

## Other features

- Forecasts should be persisted and then tested against observations day of
- human-readable output

## Potential other features

- can maybe add some measure on how distant one is from cities
- maybe subscribing to an area so you can be alerted some number of days out if conditions will be good

## Installation

- Read backend/README.md
- Read frontend/README.md

## TODO

- understand licensing
- frontend todos
- Set up production server for vuejs
- Write script to get start both servers
- Deploy to droplet
