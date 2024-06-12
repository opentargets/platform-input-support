# Open Targets: Platform-input-support overview

TODO: Write how you don't need to define `from_dict` for actions unless the
config is not shallow.

TODO: STEPS THAT NEED ETL:
  * disease
  * drug
  * expression
  * homologues
  * openfda
  * so
  * target

The aim of this application is to allow the reproducibility of OpenTarget Platform data release pipeline.
The input files are copied in a local hard disk and eventually in a specific google storage bucket

Currently, the application executes 18 steps and finally it generates the input resources for the ETL
pipeline (https://github.com/opentargets/data_pipeline)

List of available steps:
- BaselineExpression
- Disease
- Drug
- Evidence
- Expression
- Go
- Homologues
- Interactions
- Literature
- Mousephenotypes
- OpenFDA
- Otar
- Pharmacogenomics
- PPPEvidence
- Reactome
- SO
- Target
- TargetEngine

Within this application you can simply download a file from FTP, HTTP or Google Cloud Bucket but at
the same time the file can be processed in order to generate a new resource. The final files are
located under the output directory while the files used for the computation are saved under stages.

Below more details about how to execute the script.


# Running Platform Input Support

_Requires **Google Cloud SDK** and **docker** (if running locally)_

## Step 1. Configure the run
- Set the values in the [config](profiles/config.dev) or copy it to `profiles/config.<profile_name>`
- _Note: you're unlikely to need to change anything other than the PIS Config section and maybe the
  image tag._
- Set the profile to one you need:
  ```bash
  make set_profile profile=dev
  ```

## Step 2. Deploy and run the pipeline remotely
- Launch with pis arguments e.g. (steps for public):
  ```bash
  make launch_remote args='-exclude otar pppevidence'
  ```
- This deploys a vm on GCP, runs PIS with the args given, uploads the PIS output, configs and logs to
  the configured GCS bucket.
- To follow the logs while the VM is up, run the following:
  ```bash
  gcloud compute ssh \
    --zone "<pisvm.zone>" \
    --project "open-targets-eu-dev" \
    --command "journalctl -u google-startup-scripts.service -f"
    "<pisvm.username>@<pisvm.name>"
  ```

## Step 2 (alt). Run the pipeline locally
- Launch with pis arguments e.g. (steps for public):
  ```bash
  make launch_local args='-exclude otar pppevidence'
  ```
- This runs PIS with the args given, uploads the PIS output, configs and logs to the configured GCS
  bucket.

## Step 3. Clean up
- If you launched PIS remotely, you'll want to tear down the infrastructure after it's finished:
  ```bash
  make clean_infrastructure
  ```
- If you want to tear down _all_ infrastructure from previous runs:
  ```bash
  make clean_all_infrastructure
  ```
- The session configs are stored locally in "sessions/<session_id>". A helper make target allows you
- to clear this: `make clean_session_metadata` or for all sessions: `make clean_all_sessions_metadata`


# Local installation requirements

* Python3.8
* Poetry
* Apache-Jena
* git
* jq
* Google Cloud SDK

## Poetry for Linux/MAC

Installation instructions for Poetry can be found [here](https://python-poetry.org/docs/#installation).

## Running PIS via Docker image
Platform input support is available as docker image, a _Dockerfile_ is provided for building the container
image.

For instance
```bash
mkdir /tmp/pi
sudo docker run
 -v path_with_credentials:/usr/src/app/cred
 -v /tmp/pis:/usr/src/app/output
 pis_docker_image
 -steps Evidence
 -gkey /usr/src/app/cred/open-targets-gac.json
 -gb ot-team/pis_output/docker
```

When providing a Google Cloud key file, please, make sure that it is mounted within the container
at: `/srv/credentials/open-targets-gac.json`

This allows the activation of the service account when running the container image, so _gcloud-sdk_
can work with the destination Google Cloud Storage Bucket.

For using an external config file, simply add the option -c and the path where the config file is
available.

## Singularity
This is an example how to run singularity using the docker image.
```bash
singularity exec \
   -B /nfs/ftp/private/otftpuser/output_pis:/usr/src/app/output \
   docker://quay.io/opentargets/platform-input-support:cm_singularity \
   conda run --no-cature-output -n pis-py3.8 python3 /usr/src/app/platform-input-support.py -steps drug

```

## Run PIS inside EBI infrastructure
In order to run PIS inside the current EBI infrastructure the best pratice is to use Singularity
and LSF.

First of all check the google cloud account rights for the proper project.
```bash
ls -la /homes/$USER/.config/gcloud/application_default_credentials.json
```

Eventually run the following command to generate the file above:
```bash
gcloud config set project open-targets-eu-dev
```
or
```bash
gcloud config set project open-targets-prod
```

then:
```bash
gcloud auth application-default login
```

You can use `singularity/ebi.sh` to run PIS inside the EBI infrastructure.
```bash
 ./singularity docker_tag_image step google_storage_path
```

Where
* `docker_tag_image`: docker image tag (quay.io) (**under review**)
* `step` : Eg. `drug`
* `google_storage_path`: gs bucket [not mandatory]

```bash
 ./singularity/ebi.sh 21.04 drug
 ./singularity/ebi.sh 21.04 drug ot-snapshots/21.04/input
```

## Apache-Jena: Install Riot

```bash
cd ~
wget -O apache-jena.tar.gz https://www.mirrorservice.org/sites/ftp.apache.org/jena/binaries/apache-jena-4.2.0.tar.gz
tar xvf apache-jena.tar.gz --one-top-level=apache-jena --strip-components 1 -C /opt/
```

Add it to your path:

```bash
export PATH="$PATH:/opt/apache-jena/bin"
```


# Overview of config.yaml

The `config.yaml` file contains several sections. Most of the sections are used by the steps in order
to download, to extract and to manipulate the input and generate the proper output.

## Overview of configuration file sections:

### `Config`

The section `config` can be used for specify where utility programs `riot` and `jq` are installed on
the system. If the command `shutil.which` fails during PIS execution double check these configurations.

`java_vm` parameter will set up the JVM heap environment variable for the execution of the command `riot`.

### Data sources

The majority of the configuration file is specifying metadata for the execution of individual steps,
eg `tep`, `ensembl` or `drug`. These can be recognized as they all have a `gs_output_dir` key which
indicates where the files will be saved in GCP.

There is an inconsistency between keys in different steps, as they accommodate very different input
types and required levels of configuration. See [step guides](#step-guides) for configuration requirements
for specific steps. The section **config** can be used for specify where `riot` or `jq` are installed.

## A note on zip files

We are only building the functionality which we need which introduces some limitations. At present
if a zip file is downloaded we only extract one file from the archive. To configure a zip file create
an entry in the config such as:

```yaml
  - uri: https://probeminer.icr.ac.uk/probeminer_datadump.zip
    output_filename: probeminer-datadump-{suffix}.tsv.zip
    unzip_file: true
    resource: probeminer
```

The _unzip\_file_ flag tells `retrieve_resource.py` to treat the file as an archive.

The `uri` field indicates from where to download the data. The archive will be saved under `output_filename`.
The first element of the archive will be extracted under `output_filename` with the suffix '[gz|zip]'
removed, so in this case, `probeminer-datadump-{suffix}.tsv`.


# Set up application (first time)

```bash
git clone https://github.com/opentargets/platform-input-support
cd platform-input-support
poetry install
```

## Usage

```
poetry run platform_input_support -h

usage: platform_input_support [-h] [-c CONFIG] [-gkey GCP_CREDENTIALS] [-gb GCP_BUCKET] [-o OUTPUT_DIR] [-f] [-s SUFFIX] [-steps STEPS [STEPS ...]]
                              [-exclude EXCLUDE [EXCLUDE ...]] [--log-level LOG_LEVEL] [--log-config LOG_CONFIG]

Open Targets platform input support

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to config file (YAML) [env var: PIS_CONFIG] (default: None)
  -gkey GCP_CREDENTIALS, --gcp_credentials GCP_CREDENTIALS
                        The path were the JSON credential file is stored. [env var: GCP_CREDENTIALS] (default: None)
  -gb GCP_BUCKET, --gcp_bucket GCP_BUCKET
                        Copy the files from the output directory to a specific google bucket [env var: GCP_BUCKET] (default: None)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        By default, the files are generated in the root directory [env var: OT_OUTPUT_DIR] (default: None)
  -f, --force-clean     By default, the output directory is deleted. To not delete the files use this flag. [env var: OT_CLEAN_OUTPUT] (default: True)
  -s SUFFIX, --suffix SUFFIX
                        The default suffix is yyyy-mm-dd [env var: OT_SUFFIX_INPUT] (default: None)
  -steps STEPS [STEPS ...]
                        Run a specific list of sections of the config file. Eg annotations annotations_from_buckets (default: [])
  -exclude EXCLUDE [EXCLUDE ...]
                        Exclude a specific list of sections of the config file. Eg annotations annotations_from_buckets (default: [])
  --log-level LOG_LEVEL
                        set the log level [env var: LOG_LEVEL] (default: INFO)
  --log-config LOG_CONFIG
                        logging configuration file [env var: LOG_CONFIG] (default: resources/logging.ini)

Args that start with '--' can also be set in a config file (specified via -c). The config file uses YAML syntax and must represent a YAML 'mapping' (for
details, see http://learn.getgrav.org/advanced/yaml). In general, command-line values override environment variables which override config file values which
override defaults.
```

## Using Docker to run PIS during development

If you want to run PIS in a Docker container follow these steps:

1. Get the code
   ```bash
   git clone https://github.com/opentargets/platform-input-support
   ```
2. create container
   ```bash
   docker build --tag <image tag> <path to Dockerfile>
   ```
3. start container mounting the cloned code as a volume (here I assume you cloned the code into your
   home directory)
   ```bash
   docker run -v ~/platform-input-support:/usr/src/app --rm -it --entrypoint bash <image tag>
   ```
   This command will drop you into a bash shell inside the container, where you can execute the code.
4. execute code
   ```bash
   poetry run platform_input_support -steps=<step> --log-level=DEBUG
   ```


# `logging.ini`

The directory `resources` contains the file `logging.ini` with a list of default values.
If the logging.ini is not available or the user removes it than the code sets up a list of default
parameters. In both cases, the log output file is store under `log`.


# Google bucket requirements

To copy the files in a specific google storage bucket valid credentials must be used. The required
parameter `-gkey`, `--gcp_credentials` allows the specification of Google storage JSON credentials:

```bash
poetry run platform_input_support -gkey /path/open-targets-gac.json -gb bucket/object_path
```

or

```bash
poetry run platform_input_support \
  --gcp_credentials /path/open-targets-gac.json \
  --gcp_bucket ot-snapshots/es5-sufentanil/tmp
```


# More examples

```bash
poetry run platform_input_support \
  --gcp_credentials /path/open-targets-gac.json \
  --gcp_bucket ot-snapshots/es5-sufentanil/tmp \
  -steps annotations evidence \
  -exclude drug
```

```bash
poetry run platform_input_support \
  -gkey /path/open-targets-gac.json \
  -gb bucket/object_path -steps drug \
  --log-level DEBUG > log.txt
```


# Check if the files generated are corrupted

The zip files generated might be corrupted. The follow command checks if the files are correct:
```bash
find . -type f -name "*.gz" | xargs gzip -v -t
```


# Step guides

The program is broken into steps such as `drug`, `interactions`, etc. Each step can be configured as
necessary in the config file and run using command line arguments.

## EFO step (disease)

The EFO step is used to gather the raw data for the [platform ETL](https://github.com/opentargets/platform-etl-backend).

The scope this step is supporting the annotation, analysis and visualization of data handled by the
core ontology for Open Targets.

This step downloads and manipulates the input files and it generates the following output:
* `ontology-efo-v3.xx.yy.jsonl`: list of EFO terms
* `ontology-mondo.jsonl`: list of MONDO terms
* `ontology-hpo.jsonl`: list of HPO terms
* `hpo-phenotypes-_yyyy-mm-dd_.jsonl`: mapping between CrossReference databaseId

## Drug step

The Drug step is used to gather the raw data for the [platform ETL](https://github.com/opentargets/platform-etl-backend).

ChEMBL made an Elasticsearch instance available for querying. To keep data volumes and running times
down specify the index and fields which are required in the config file.

## Homology Step

This step is used to download raw json data from the ENSEMBL [ftp server](https://ftp.ensembl.org/pub/current_json/)
for specified species.

These inputs are then processed with `jq` to extract the id and name field which are required by the
ETL. The downloaded json files approach 30GB in size, and we only extract ~10MB from them. It is worth
considering if we want to retain these files long-term.

## HPA Expression Step

This step is used to download data from the internal OT resources and protenatlas information.

The
tissue translation map requires some manipulations due the weird JSON format. All the files generated
are required by the ETL.

## OpenFDA FAERs

This step collects adverse events of interest from [OpenFDA FAERS](https://open.fda.gov/data/faers/).

It requires two input parameters via the configuration file:
- URL of the events black list
- URL of OpenFDA FAERS repository metadata in JSON format

## OTAR

This step collects two types of information on OTAR Projects, used in the internal platform:

1. **Metadata** information on the projects
2. **Mapping** information between the projects and diseases


# Application architecture

- `platform-input-support` is the entrypoint to the program; it loads the `config.yaml` which specifies
  the available steps and any necessary configuration which goes with them. This configuration is
  represented internally as a dictionary.
- Platform input support configures a `RetrieveResource` object and calls the `run` method triggering
  the selected steps.
- `RetrieveResource` will consult the steps selected and trigger a method for each selected step. Most
  steps will defer to a helper object in `Modules` to retrieve the selected resources.
