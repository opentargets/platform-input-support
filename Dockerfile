# Description: Dockerfile for the platform_input_support package
#
# To run locally, you must have a credentials file for GCP. Assuming you do,
# you can run the following command:
#
# docker run -v /path/to/credentials.json:/app/credentials.json -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json pis -s so


FROM python:3.12.4-alpine3.20

WORKDIR /app

COPY pyproject.toml requirements.txt README.md config.yaml ./

COPY platform_input_support ./platform_input_support

RUN pip install --no-deps -r requirements.txt && pip install --no-deps .

ENTRYPOINT ["platform_input_support"]
CMD []
