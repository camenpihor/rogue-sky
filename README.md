# RogueSky

## Installation

1. `cp .sample_env .env` copy and and fill out the anything in `<>` in the .env file
    1. `DARKSKY_API_KEY` DarkSky secret key from your [DarkSky developer account](https://darksky.net/dev/account)
    2. `DATABASE_URL` postgres database url to be created and used for development
    3. `TEST_DATABASE_URL` postgres database url to be created and used for tests
2. `set -o allexport && source .env && set +o allexport` to export environment variables
3. `python setup.py install` to install package
4. `pip install -r requirements.testing.in` to install testing requirements
5. `scripts/setup-db` to set up production and test databases
6. `scripts/test` to verify install

## Examples

Check out `examples/playing_around.ipynb`!

## TODOs

- geopy is slow :(
- is there a faster/cleaner address geopy parser?
- is there another geopy-like thing? maybe just hit google maps api?
- how to best parse address
- should I return city, state, or entire address?
