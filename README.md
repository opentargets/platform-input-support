# Open Targets: Platform-input-support overview

The aim of this application is to allow the reproducibility of OpenTarget Platform data release pipeline.
The input files are copied in a local hard disk and eventually in a specific google storage bucket.

Currently, the application executes 11 steps and finally it generates the input resources for
the [ETL pipeline](https://github.com/opentargets/platform-etl-backend).

List of available steps:

- Disease
- Drug
- Evidence
- Expression
- Go
- Homologues
- Interactions
- Mousephenotypes
- OpenFDA
- Reactome
- SO
- Target
- Literature
- Otar

Within this application you can simply download a file from FTP, HTTP or Google Cloud Bucket but at the same time the
file can be processed in order to generate a new resource.

The final files are located under the output directory while the files used for the computation are saved under stages.

# Installation

There are two recommended ways to run PIS: either with a local installation or via a Docker container.

## VM installation

The following utilities must be installed:

* Conda
* Apache-Jena
* git
* jq
* curl
* Google Cloud SDK

## Install dependencies

### Conda for Linux/MAC

Conda provides an isolated environment for Python dependencies. Download Conda3
for [Mac](download Anaconda3-2021.05-MacOSX-x86_64.sh) or [Linux](download Anaconda3-2021.05-Linux-x86_64.sh) as
appropriate.

Conda can be installed with the following commands:

```bash
wget https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
bash path_where_downloaded_the_file/Anaconda3-2020.07-Linux-x86_64.sh
source ~/.bashrc
conda update
```

Now that Conda is installed we need to create the environment which holds the necessary Python dependencies:

```bash
git clone https://github.com/opentargets/platform-input-support
cd platform-input-support
conda env create -f environment.yaml
conda activate pis-py3.8
```

### Other utilities

The following command will install the required utilities:

```bash
    apt install -y curl jq openjdk-11-jre-headless apt-transport-https ca-certificates gnupg; \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list ; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | tee /usr/share/keyrings/cloud.google.gpg ; \
    apt update; \
    apt install -y google-cloud-cli; \
    mkdir /tmp && cd /tmp; \
    wget --no-check-certificate -O apache-jena.tar.gz https://archive.apache.org/dist/jena/binaries/apache-jena-4.4.0.tar.gz; \
    tar xvf apache-jena.tar.gz --one-top-level=apache-jena --strip-components 1 -C /usr/share/
```

## Docker

Running via Docker image does not require the installation of any dependencies apart from Docker.

Platform input support is available as docker image, a _Dockerfile_ is provided for building the container image.

Running PIS using Docker requires the specification of where the container should save the (a) outputs and optionally (
b) logs, as well as where to find the (c) credentials key.

```bash
mkdir /tmp/pis
sudo docker run 
 -v path_with_credentials:/usr/src/app/cred #(c)
 -v /tmp/pis:/usr/src/app/output #(a)
 pis_docker_image 
 -steps Evidence 
 -gkey /usr/src/app/cred/open-targets-gac.json # note this references (c)
 -gb ot-team/pis_output/docker
```

When providing a Google Cloud key file, please, make sure that it is mounted within the container at this exact mount
point

```
/srv/credentials/open-targets-gac.json
```

This allows the activation of the service account when running the container image, so _gcloud-sdk_ can work with the
destination Google Cloud Storage Bucket.

For using an external config file, simply add the option -c and the path where the config file is available

### Conda in Docker (for PyCharm)

A Docker container can be used to provide a local development environment which will match what is going to be used in
production.

```
# build the image
docker build --tag pis-py3.8 <path to Dockerfile>
```

You can use the Docker image from within PyCharm by selecting 'Add Interpreter -> Docker -> <image>'

# Usage

The program `platform-input-support` includes a detailed help message (see with `python platform-input-support.py -h`):

```bash
conda activate pis-py3.8
cd your_path_application
python platform-input-support -h
usage: platform-input-support.py [-h] [-c CONFIG]
                                 [-gkey GCP_CREDENTIALS]
                                 [-gb GCP_BUCKET] [-o OUTPUT_DIR] [-t]
                                 [-s SUFFIX] [-steps STEPS [STEPS ...]]
                                 [-exclude EXCLUDE [EXCLUDE ...]] [--skip]
                                 [-l] [--log-level LOG_LEVEL]
                                 [--log-config LOG_CONFIG]

...

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to config file (YAML) [env var: CONFIG] (default:
                        None)
  -gkey GOOGLE_CREDENTIAL_KEY, --gcp_credentials GOOGLE_CREDENTIAL_KEY
                        The path were the JSON credential file is stored. [env
                        var: GCP_CREDENTIALS] (default: None)
  -gb GCP_BUCKET, --gcp_bucket GCP_BUCKET
                        Copy the files from the output directory to a specific
                        google bucket (default: None)
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        By default, the files are generated in the root
                        directory [env var: OT_OUTPUT_DIR] (default: None)
  -t, --thread          Run the script with thread [env var: OT_THREAD]
                        (default: False)
  -s SUFFIX, --suffix SUFFIX
                        The default suffix is yyyy-mm-dd [env var:
                        OT_SUFFIX_INPUT] (default: None)
  -steps STEPS [STEPS ...]
                        Run a specific list of sections of the config file. Eg
                        annotations annotations_from_buckets (default: None)
  -exclude EXCLUDE [EXCLUDE ...]
                        Exclude a specific list of sections of the config
                        file. Eg annotations annotations_from_buckets
                        (default: None)
  --skip                Skip the errors and just report them (default: False)
  -l, --list_steps      List of steps callable (default: False)
  --log-level LOG_LEVEL
                        set the log level [env var: LOG_LEVEL] (default: INFO)

```

## Google bucket requirements

To copy the files in a specific google storage bucket valid credentials must be used.
The required parameter -gkey (--gcp_credentials) allows the specification of Google storage JSON credential.
Eg.

```bash
python platform-input-support.py -gkey /path/open-targets-gac.json -gb bucket/object_path
# or
python platform-input-support.py
         --gcp_credentials /path/open-targets-gac.json
         --gcp_bucket ot-snapshots/es5-sufentanil/tmp
```

## More examples

```bash
# run all steps and ignore failures
python platform-input-support.py
         --skip
         --gcp_credentials /path/open-targets-gac.json
         --gcp_bucket ot-snapshots/es5-sufentanil/tmp
 # run all steps except drug
 python platform-input-support.py
         --skip
         --gcp_credentials /path/open-targets-gac.json
         --gcp_bucket ot-snapshots/es5-sufentanil/tmp
         --exclude drug        

# run only steps annotations and evidence
python platform-input-support.py
         --gcp_credentials /path/open-targets-gac.json
         --gcp_bucket ot-snapshots/es5-sufentanil/tmp
         -steps annotations evidence
# run specific step with log level set to debug
python platform-input-support.py
         -gkey /path/open-targets-gac.json
         -gb bucket/object_path -steps drug
         --log-level DEBUG
```

# Configuration

The *config.yaml* file contains several sections. Most of the sections are used by the steps in order to download,
to extract and to manipulate the input and generate the proper output.

## Overview of configuration file sections:

### Config

The section **config** can be used for specify where utility programs `riot` and `jq` are installed on the system.
If the command shutil.which fails during PIS execution double check these configurations.

_**"java_vm"**_ parameter will set up the JVM heap environment variable for the execution of the command `riot`.

### Data sources

The majority of the configuration file is specifying metadata for the execution
of individual steps, eg `tep`, `ensembl` or `drug`. These can be recognised as they
all have a `gs_output_dir` key which indicates where the files will be saved in GCP.

There is inconsistency between keys in different steps, as they accommodate very different
input types and required levels of configuration. See [step guides](#step-guides) for
configuration requirements for specific steps.
The section **config** can be used for specify where `riot` or `jq` are installed.

## A note on zip files

We are only building the functionality which we need which introduces some limitations. At present if a zip file is
downloaded
we only extract _1_ file from the archive. To configure a zip file create an entry in the config such as:

```yaml
  - uri: https://probeminer.icr.ac.uk/probeminer_datadump.zip
    output_filename: probeminer-datadump-{suffix}.tsv.zip
    unzip_file: true
    resource: probeminer
```

The _unzip\_file_ flag tells `RetrieveResource.py` to treat the file as an archive.

The `uri` field indicates from where to download the data. The archive will be saved under `output_filename`. The first
element of the archive will be extracted under `output_filename` with the suffix '[gz|zip]' removed, so in this case, _
probeminer-datadump-{suffix}.tsv_.

## Logging

The directory **"resources"** contains the file `logging.ini` with a list of default value.
If the `logging.ini` is not available or the user removes it than the code sets up a list of default parameters.
In both case, the log output file is store under **"log"**.

# Step guides

The program is broken into steps such as `drug`, `interactions`, etc. Each step can be configured as necessary in the
config file and run using command line arguments.

## EFO step (disease)

The EFO step is used to gather the raw data for the [platform ETL](https://github.com/opentargets/platform-etl-backend).

The scope of EFO is to support the annotation, analysis and visualization of data handled by the core ontology for Open
Targets.

This step downloads and manipulates the input files and it generates the following output:

* ontology-efo-v3.xx.yy.jsonl : list of EFO terms
* ontology-mondo.jsonl : list of MONDO terms
* ontology-hpo.jsonl : list of HPO terms
* hpo-phenotypes-_yyyy-mm-dd_.jsonl : mapping between CrossReference databaseId

## Drug step

The Drug step is used to gather the raw data for the [platform ETL](https://github.com/opentargets/platform-etl-backend)
.

ChEMBL have made an Elasticsearch instance available for querying. To keep data volumes and running times down specify
the
index and fields which are required in the config file.

## Homology Step

This step is used to download raw json data from the ENSEMBL [ftp server](https://ftp.ensembl.org/pub/current_json/) for
specified species. These inputs are then processed with `jq` to extract the id and name fields which are required by the
ETL. The downloaded json files approach 30GB in size, and we only extract ~10MB from them. It is worth considering if we
want to retain these files long-term.

## Hpa Expression Step

This step is used to download data from the internal OT resources and proteinatlas information.
The tissue translation map requires some manipulations due the weird JSON format.
All the files generated are required by the ETL.

## OpenFDA FAERs

This step collects adversed events of interest from [OpenFDA FAERS](https://open.fda.gov/data/faers/).
It requires two input parameters via the configuation file:

- URL of the events black list.
- URL where to find OpenFDA FAERS repository metadata in JSON format.

## OTAR

This step collects two kinds of information on OTAR Projects, used in the internal platform:

1. **Metadata** information on the projects.
2. **Mapping Information**, between the projects and diseases

# Application architecture

- `platform-input-support` is the entrypoint to the program; it loads the `config.yaml` which specifies the available
  steps and any necessary configuration which goes with them. This configuration is represented internally as a
  dictionary.
  Platform input support configures a `RetrieveResource` object and calls the `run` method triggering the selected
  steps.
- `RetrieveResource` will consult the steps selected and trigger a method for each selected step. Most steps will defer
  to a helper object in `Modules` to retrieve the selected resources.

# Internal OT release recipe

- Start a VM on GCP - recommended `n2-standard-16`
- Clone repository
- Get credentials file
- Set `gcloud auth login <pis_profile>`
- Update `config.yaml` with latest release values.
    - ensembl id
    - efo version
    - See `git log -p --stat -- config.yaml` for how file has been updated in the past.
- start tmux session so we can detach shell and do other things `tmux a -t pis`
- Run with Docker, configuring the output, log and credential volumes:

```bash
`docker run \
  -v $(pwd)/tmp/output:/srv/output \
  -v $(pwd)/logs:/usr/src/app/log \
  -v $HOME/data/credentials/open-targets-gac.json:/srv/credentials/open-targets-gac.json \
  otpis -0 /srv/output --log-level=DEBUG \
  -gkey /srv/credentials/open-targets-gsc.json \
  -gb open-targets-pre-data-releases/22.12-docker \
  -exclude otar
```

## Beware

- Find out the Ensembl and EFO versions to use from the data team. They are _not_ necessarily the latest.
- String interactions (interactions-inputs) `9606.protein.links.full_w_homology.v11.5.txt.gz` needs to be collected
  manually. Confirm with the data team whether this has been updated. Typically, we use the file from the previous
  release.
