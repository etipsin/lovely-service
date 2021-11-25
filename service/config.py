from os import environ

en = environ.get


def boolean(value: str):
    if value.lower() in ("", "0", "false"):
        return False

    return True


class Config:
    HOST = en("SERVICE_HOST", "0.0.0.0")
    PORT = en("SERVICE_PORT", "8080")

    ELK_ENABLE = boolean(en("SERVICE_ELK_ENABLE", "FALSE"))
    SWAGGER_ENABLE = boolean(en("SERVICE_SWAGGER_ENABLE", "TRUE"))

    # ELK
    ELK_HOST = en("SERVICE_ELK_HOST", "localhost")
    ELK_PORT = en("SERVICE_ELK_PORT", "5000")
    ELK_LEVEL = en("SERVICE_ELK_LEVEL", "INFO")
    ELK_LOGGER_NAME = en("SERVICE_ELK_LOGGER_NAME", "elk")
    ELK_SERVICE_NAME = en("SERVICE_ELK_SERVICE_NAME", "service")

    # Postgres
    POSTGRES_DSN = en("SERVICE_POSTGRES_DSN", "")
    POSTGRES_MIN_SIZE = en("SERVICE_POSTGRES_MIN_SIZE", "5")
    POSTGRES_MAX_SIZE = en("SERVICE_POSTGRES_MAX_SIZE", "75")

    # Sentry
    SENTRY_ENABLE = boolean(en("SERVICE_SENTRY_ENABLE", "TRUE"))
    SENTRY_DSN = en("SERVICE_SENTRY_DSN", "")
