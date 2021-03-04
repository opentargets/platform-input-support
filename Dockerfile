FROM continuumio/miniconda3

ARG conda_env=pis-py3

COPY environment.yaml .

RUN conda update -n base -c defaults conda
RUN conda env create --file environment.yaml
ENV PATH /opt/conda/envs/$conda_env/bin:$PATH

#put the application in the right place
WORKDIR /usr/src/app
COPY . /usr/src/app

ENTRYPOINT [ "/bin/bash" ]