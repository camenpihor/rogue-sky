# Backend

## Installation

1. `cp .sample_env .env` copy and and fill out the anything in `<>` in the .env file
    1. `DARKSKY_API_KEY` DarkSky secret key from your [DarkSky developer account](https://darksky.net/dev/account)
    2. `DATABASE_URL` postgres database url to be created and used for development
    3. `TEST_DATABASE_URL` postgres database url to be created and used for tests
2. `set -o allexport && source .env && set +o allexport` to export environment variables
3. `pip install -r requirements.txt` to install requirements
4. `scripts/setup-db` to set up production and test databases
5. `scripts/test` to verify install

## Examples

Check out `examples/playing_around.ipynb`!
