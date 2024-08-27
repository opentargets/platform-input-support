# Description: Dockerfile for the platform_input_support package
#
# To run locally, you must have a credentials file for GCP. Assuming you do,
# you can run the following command:
#
# docker run -v /path/to/credentials.json:/app/credentials.json -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json pis -s so

FROM python:3.12.4-alpine3.20
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ADD . /app

WORKDIR /app
RUN uv sync --frozen

ENTRYPOINT ["uv", "run", "platform_input_support"]
