from secrets import token_urlsafe

from starlette.config import Config

# Config will be read from environment variables and/or ".env" files.
from starlette.datastructures import Secret

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
TESTING = config("TESTING", cast=bool, default=False)
HTTPS_ONLY = config("HTTPS_ONLY", cast=bool, default=False)
GZIP_COMPRESSION = config("GZIP", cast=bool, default=False)
SECRET = config("SECRET", cast=Secret, default=token_urlsafe(10))

DB_USER = config("POSTGRES_USER", cast=str)
DB_PASSWORD = config("POSTGRES_PASSWORD", cast=str)
DB_HOST = config("POSTGRES_SERVER", cast=str)
DB_PORT = config("POSTGRES_PORT", cast=str)
DB_NAME = config("POSTGRES_DB", cast=str)

GENERATE_SCHEMAS = config("GENERATE_SCHEMAS", cast=bool, default=True)

# The Sentry DSN is a unique identifier for our app when connecting to Sentry
# See https://docs.sentry.io/platforms/python/#connecting-the-sdk-to-sentry
SENTRY_DSN = config("SENTRY_DSN", cast=str, default="")
RELEASE_VERSION = config("RELEASE_VERSION", cast=str, default="<local dev>")

if SENTRY_DSN:  # pragma: nocover
    import sentry_sdk

    sentry_sdk.init(dsn=SENTRY_DSN, release=RELEASE_VERSION)

if DEBUG:
    DB_URL = "sqlite://db.sqlite"
else:
    DB_URL=f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"