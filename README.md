# Cloud Storage API

REST API for a cloud file storage service.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose

## Installation

Clone the repository:

```shell
git clone https://gitlab.com/pet777/cloud-storage/cloud-storage-api.git
cd cloud-storage-api
```

Install dependencies:

```shell
uv sync
```

Create `.env` from the example:

```shell
cp .env.example .env
```

The default `.env.example` is configured for running the backend **inside Docker**:
the `postgres`, `redis`, and `rustfs` hosts are container names from `docker-compose.yml`.

- **Backend in Docker:** use `.env` as is.
- **Backend on the host:** replace the `postgres`, `redis`, and `rustfs` hosts with `localhost` in `.env`.

## Prepare infrastructure

These steps are required for both ways of running the application.

Start infrastructure:

```shell
docker compose up -d postgres redis rustfs
```

Apply database migrations:

```shell
POSTGRES__HOST=localhost \
REDIS__HOST=localhost \
RUSTFS__HOST=localhost \
uv run alembic upgrade head
```

> **Note:** Migrations always run from the host, so the hosts are overridden with `localhost`
> in the command.

## Run the application

Choose one of the options below.

### Option 1: Locally

Make sure `.env` uses `localhost` hosts (see [Installation](#installation)), then run:

```shell
uv run uvicorn cloud_storage.main:app --reload
```

### Option 2: In Docker

Build the image:

```shell
docker build -t cloud-storage/backend:latest .
```

Start the backend:

```shell
docker compose up -d backend
```

> **Note:** The image tag must match the `image` of the `backend` service in `docker-compose.yml`.

## Usage

Once the application is running:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

## Stop

Stop all containers:

```shell
docker compose down
```

To also remove volumes with data:

```shell
docker compose down -v
```

## Tests

Tests use [Testcontainers](https://testcontainers.com/) and start the required infrastructure
automatically, so you don't need to run `docker compose` beforehand. Docker must be running.

Run tests with coverage:

```shell
uv run pytest --cov=src
```