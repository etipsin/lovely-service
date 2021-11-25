# Your Lovely Service

## Environment Variables

```
SERVICE_HOST
SERVICE_PORT

SERVICE_ELK_ENABLE
SERVICE_SWAGGER_ENABLE

# ELK
SERVICE_ELK_HOST
SERVICE_ELK_PORT
SERVICE_ELK_LEVEL
SERVICE_ELK_LOGGER_NAME
SERVICE_ELK_SERVICE_NAME

# Postgres
SERVICE_POSTGRES_DSN
SERVICE_POSTGRES_MIN_SIZE
SERVICE_POSTGRES_MAX_SIZE

# Sentry
SERVICE_SENTRY_ENABLE
SERVICE_SENTRY_DSN
```

## Build Image

```
docker build -t service:1.0.0 -f Dockerfile .
```

## Run Image

```
docker run -p 8080:8080 service:1.0.0
```

## Test It Local

#### Building
```
docker-compose build
```

#### Running
```
docker-compose run
```

#### Swagger
```
http://localhost:8080/doc
```