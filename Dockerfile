# Description: Dockerfile for the platform_input_support package
#
# To run locally, you must have a credentials file for GCP. Assuming you do,
# you can run the following command:
#
# docker run -v /path/to/credentials.json:/app/credentials.json -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json pis -s so


FROM python:3.12.4-alpine3.20

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock README.md config.yaml ./

ENV POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_CACHE_DIR=/tmp/poetry_cache

COPY platform_input_support ./platform_input_support

RUN poetry install --only=main

ENTRYPOINT ["poetry", "run", "platform_input_support"]
CMD []
