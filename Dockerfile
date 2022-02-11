FROM continuumio/miniconda3

# Update sources
RUN apt update


ARG conda_env=pis-py3.8

COPY environment.yaml .

RUN conda update -n base -c defaults conda
RUN conda env create --file environment.yaml
ENV PATH /opt/conda/envs/$conda_env/bin:$PATH

ENTRYPOINT [ "/bin/bash" ]
#put the application in the right place
WORKDIR /usr/src/app
COPY . /usr/src/app

# install helper utilities, including Apache Jena (RIOT provider)
RUN apt install -y jq openjdk-11-jre-headless; \
    mkdir /tmp; \
    cd /tmp; \
    wget --no-check-certificate -O apache-jena.tar.gz https://www.mirrorservice.org/sites/ftp.apache.org/jena/binaries/apache-jena-4.4.0.tar.gz; \
    tar xvf apache-jena.tar.gz --one-top-level=apache-jena --strip-components 1 -C /usr/share/
ENTRYPOINT [ "docker-script/entrypoint.sh" ]