FROM python:3.8.18-slim-bullseye

# install helper utilities, including Apache Jena (RIOT provider)
RUN apt update; \
    apt install -y curl wget jq openjdk-11-jre-headless apt-transport-https ca-certificates gnupg
RUN mkdir /tmp; \
    cd /tmp; \
    wget --no-check-certificate -O apache-jena.tar.gz https://archive.apache.org/dist/jena/binaries/apache-jena-4.4.0.tar.gz; \
    tar xvf apache-jena.tar.gz --one-top-level=apache-jena --strip-components 1 -C /usr/share/; \
    rm apache-jena.tar.gz
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-cli -y   


# Copy the pipeline source tree
COPY . /usr/src/app

# Configure Poetry
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Set working dir
WORKDIR /usr/src/app

# Install python dependencies
RUN poetry install

# Running the container
ENTRYPOINT [ "docker-script/entrypoint.sh" ]