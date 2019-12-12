# RogueSky

## Installation

1. `cp .sample_env .env` copy and and fill out the anything in `<>` in the .env file
    1. `DARKSKY_API_KEY` DarkSky secret key from your [DarkSky developer account](https://darksky.net/dev/account)
2. `set -o allexport && source .env && set +o allexport` to export environment variables
3. `python setup.py install` to install package
4. `pip install -r requirements.testing.in` to install testing requirements
6. `scripts/test` to verify install

## Examples

Check out `examples/playing_around.ipynb`!

## TODOs

- geopy is slow :(
- should I return city, state, or entire address?
