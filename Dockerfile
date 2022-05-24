FROM continuumio/miniconda3

# install helper utilities, including Apache Jena (RIOT provider)
RUN apt update; \
    apt install -y curl jq openjdk-11-jre-headless apt-transport-https ca-certificates gnupg; \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list ; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | tee /usr/share/keyrings/cloud.google.gpg ; \
    apt update; \
    apt install -y google-cloud-cli ; \
    mkdir /tmp; \
    cd /tmp; \
    wget --no-check-certificate -O apache-jena.tar.gz https://archive.apache.org/dist/jena/binaries/apache-jena-4.4.0.tar.gz; \
    tar xvf apache-jena.tar.gz --one-top-level=apache-jena --strip-components 1 -C /usr/share/

ARG conda_env=pis-py3.8

COPY environment.yaml .

RUN conda update -n base -c defaults conda
RUN conda env create --file environment.yaml
ENV PATH /opt/conda/envs/$conda_env/bin:$PATH

ENTRYPOINT [ "/bin/bash" ]
#put the application in the right place
WORKDIR /usr/src/app
COPY . /usr/src/app

ENTRYPOINT [ "docker-script/entrypoint.sh" ]