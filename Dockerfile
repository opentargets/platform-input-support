FROM continuumio/miniconda3:23.3.1-0

# install helper utilities, including Apache Jena (RIOT provider)
RUN apt update; \
    apt install -y curl jq openjdk-11-jre-headless apt-transport-https ca-certificates gnupg
RUN mkdir /tmp; \
    cd /tmp; \
    wget --no-check-certificate -O apache-jena.tar.gz https://archive.apache.org/dist/jena/binaries/apache-jena-4.4.0.tar.gz; \
    tar xvf apache-jena.tar.gz --one-top-level=apache-jena --strip-components 1 -C /usr/share/
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-cli -y   


# Copy the pipeline source tree
COPY . /usr/src/app

# Prepare conda environment
ARG conda_env=otpis
RUN cd /usr/src/app; conda update -n base -c defaults conda
RUN cd /usr/src/app; conda env create --file environment.yaml

# Running the container
ENV PATH /opt/conda/envs/$conda_env/bin:$PATH
WORKDIR /usr/src/app
ENTRYPOINT [ "docker-script/entrypoint.sh" ]