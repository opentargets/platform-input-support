FROM continuumio/miniconda3

# Update sources
RUN apt update

ARG conda_env=pis-py3

COPY environment.yaml .

RUN conda update -n base -c defaults conda
RUN conda env create --file environment.yaml
ENV PATH /opt/conda/envs/$conda_env/bin:$PATH

ENTRYPOINT [ "/bin/bash" ]
#put the application in the right place
WORKDIR /usr/src/app
COPY . /usr/src/app

# install helper utilities
RUN apt install -y jq

ENTRYPOINT [ "docker-script/entrypoint.sh" ]