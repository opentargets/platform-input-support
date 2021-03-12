# Open Targets: Platform-input-support overview

The aim of this application is to allow the reproducibility of OpenTarget Platform data release pipeline.
The input files are copied in a specific google storage bucket.

Currently, the application executes 13 steps and finally it generates a Yaml config file that can be used to run the
the OT pipeline (https://github.com/opentargets/data_pipeline)

List of available steps:
- annotations
- annotations_from_buckets
- chemical_probes
- drug
- eco
- efo
- ensembl
- evidence
- homologues
- hpa  
- interactions
- known_target_safety
- tep


The step 'evidences' uploads the last evidences from different providers and 
generates a subset of these evidences using the file `minimal_ensembl.txt`

Below more details about how to execute the script.

# Installation Requirements

* Conda
* Apache-Jena
* git

## Conda for Linux/MAC

Download Conda3 for Mac here: <br>
 https://www.anaconda.com/products/individual <br>
[download Anaconda3-2020.07-MacOSX-x86_64.sh]

Download Conda3 for Linux x86_84 <br>
 https://www.anaconda.com/products/individual <br>
[download Anaconda3-2020.07-Linux-x86_64.sh]

Conda: installation commands
```
bash path_where_downloaded_the_file/Anaconda3-2020.07-Linux-x86_64.sh
source ~/.bashrc
conda update
```
Eg. for linux
```
wget https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
bash Anaconda3-2020.07-Linux-x86_64.sh
source ~/.bashrc
```
## Conda in Docker (for PyCharm)

If you would rather run a containerised version of Conda use the provided Dockerfile. 

```
# build the image
docker build --tag pis-py3 <path to Dockerfile>
```
You can use the Docker image from within PyCharm by selecting 'Add Interpreter -> Docker -> <image>'


## Singularity 
This is an example how to run singularity using the docker image.
``` shell
singularity exec \
   -B /nfs/ftp/private/otftpuser/output_pis:/usr/src/app/output \
   docker://quay.io/opentargets/platform-input-support:cm_singularity \
   conda run --no-capture-output -n pis-py3 python3 /usr/src/app/platform-input-support.py -steps drug
  
```

## Run PIS inside EBI infrastructure
In order to run PIS inside the current EBI infrastructure the best praticse is to use Singularity and LSF.

First of all check the google cloud account rights for the proper project.
```shell
ls -la /homes/$USER/.config/gcloud/application_default_credentials.json
```

Eventually run the following command to generate the file above:
```shell
gcloud config set project open-targets-eu-dev
or
gcloud config set project open-targets-prod

gcloud auth application-default login
```
You can use `singularity/ebi.sh` to run PIS inside the EBI infrastructure.
```
 ./singularity docker_tag_image step google_storage_path 
```
where 
* docker_tag_image: docker image tag (quay.io)
* step : Eg. drug 
* google_storage_path: gs bucket [not mandatory]

```shell
 ./singularity/ebi.sh 21.04 drug 
 
 ./singularity/ebi.sh 21.04 drug ot-snapshots/21.04/input

```


## Apache-Jena : Install Riot
```
cd ~
wget -O apache-jena.tar.gz https://www.mirrorservice.org/sites/ftp.apache.org/jena/binaries/apache-jena-3.16.0.tar.gz
tar xvf apache-jena.tar.gz --one-top-level=apache-jena --strip-components 1

Add ~/apache-jena/bi to .bashrc
EG.
export PATH="$PATH:/your_path/apache-jena/bin"

source .bashrc

```
# Overview of config.yaml

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

### Data pipeline schema

`data_pipeline_schema` is a kind of summary output which lists where outputs were saved 
and in some cases which inputs were used. This is to assist in generating configuration
files for client programs like the data pipeline or ETL.

## A note on zip files

We are only building the functionality which we need which introduces some limitations. At present if a zip file is downloaded 
we only extract _1_ file from the archive. To configure a zip file create an entry in the config such as:

```yaml
  - uri: https://probeminer.icr.ac.uk/probeminer_datadump.zip
    output_filename: probeminer-datadump-{suffix}.tsv.zip
    unzip_file: true
    resource: probeminer
```
The _unzip\_file_ flag tells `RetrieveResource.py` to treat the file as an archive.

The `uri` field indicates from where to download the data. The archive will be saved under `output_filename`. The first
element of the archive will be extracted under `output_filename` with the suffix '[gz|zip]' removed, so in this case, _probeminer-datadump-{suffix}.tsv_.

# Set up application (first time)
```
git clone https://github.com/opentargets/platform-input-support
cd platform-input-support
conda env create -f environment.yaml
conda activate pis-py3

python platform-input-support.py -h
```

## Usage

```
conda activate pis-py3
cd your_path_application
python platform-input-support -h
usage: platform-input-support.py [-h] [-c CONFIG]
                                 [-gkey GOOGLE_CREDENTIAL_KEY]
                                 [-gb GOOGLE_BUCKET] [-o OUTPUT_DIR] [-t]
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
  -gkey GOOGLE_CREDENTIAL_KEY, --google_credential_key GOOGLE_CREDENTIAL_KEY
                        The path were the JSON credential file is stored. [env
                        var: GOOGLE_APPLICATION_CREDENTIALS] (default: None)
  -gb GOOGLE_BUCKET, --google_bucket GOOGLE_BUCKET
                        Copy the files from the output directory to a specific
                        google bucket (default: None)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
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

# Logging.ini
The directory **"resources"** contains the file logging.ini with a list of default value.
If the logging.ini is not available or the user removes it than the code sets up a list of default parameters.
In both case, the log output file is store under **"log"**


# Google bucket requirements
To copy the files in a specific google storage bucket valid credentials must be used.
The required parameter -gkey (--google_credential_key) allows the specification of Google storage JSON credential.
Eg.
```
python platform-input-support.py -gkey /path/open-targets-gac.json -gb bucket/object_path
or
python platform-input-support.py
         --google_credential_key /path/open-targets-gac.json
         --google_bucket ot-snapshots/es5-sufentanil/tmp
```

# More examples

```
python platform-input-support.py
         --skip
         --google_credential_key /path/open-targets-gac.json
         --google_bucket ot-snapshots/es5-sufentanil/tmp
or  
python platform-input-support.py
         --google_credential_key /path/open-targets-gac.json
         --google_bucket ot-snapshots/es5-sufentanil/tmp
         -steps annotations evidence
         -exclude drug
or
python platform-input-support.py
         -gkey /path/open-targets-gac.json
         -gb bucket/object_path -steps drug
         --log-level DEBUG > log.txt
```

### Check if the files generated are corrupted
The zip files generated might be corrupted. The follow command checks if the files are correct.
sh check_corrupted_files.sh

### Installation command for Google Cloud or Amazon Azure
Create a linux VM server and run the following commands
```
sudo apt update
sudo apt install git
sudo apt-get install bzip2 wget
```
```
wget https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
bash Anaconda3-2020.07-Linux-x86_64.sh
source ~/.bashrc

```

```
mkdir gitRepo
cd gitRepo
git clone https://github.com/opentargets/platform-input-support.git
cd platform-input-support
conda env create -f environment.yaml
conda activate pis-py3
python platform-input-support.py -l
```

Use nohup to avoid that the process hang up.

```nohup python platform-input-support.py [options] &

Eg.
nohup python platform-input-support.py
         -gkey /path/open-targets-gac.json
         -gb bucket/object_path -steps drug
         --log-level DEBUG > log.txt &
```

# Step guides

The program is broken into steps such as `drug`, `interactions`, etc. Each step can be configured as necessary in the 
config file and run using command line arguments. 

## EFO step (disease)

The EFO step is used to gather the raw data for the [platform ETL](https://github.com/opentargets/platform-etl-backend).

The scope of EFO is to support the annotation, analysis and visualization of data handled by the core ontology for Open Targets. 

This step downloads and manipulates the input files and it generates the following output:
* ontology-efo-v3.xx.yy.jsonl : list of EFO terms
* ontology-mondo.jsonl : list of MONDO terms
* ontology-hpo.jsonl : list of HPO terms
* hpo-phenotypes-_yyyy-mm-dd_.jsonl : mapping between CrossReference databaseId

## Drug step

The Drug step is used to gather the raw data for the [platform ETL](https://github.com/opentargets/platform-etl-backend).

ChEMBL have made an Elasticsearch instance available for querying. To keep data volumes and running times down specify the
index and fields which are required in the config file.

ChEMBL's ES instance is only available from within the EMBL-EBI VPN. If you need to run this step it is necessary that you
use a machine that is connected to the VPN network. 

## Homology Step

This step is used to download raw json data from the ENSEMBL [ftp server](https://ftp.ensembl.org/pub/current_json/) for 
specified species. These inputs are then processed with `jq` to extract the id and name fields which are required by the 
ETL. The downloaded json files approach 30GB in size, and we only extract ~10MB from them. It is worth considering if we
want to retain these files long-term. 

## Hpa Expression Step

This step is used to download data from the internal OT resources and proteinatlas information.
The tissue translation map requires some manipulations due the weird JSON format.
All the files generated are required by the ETL.



# Application architecture

- `platform-input-support` is the entrypoint to the program; it loads the `config.yaml` which specifies the available
steps and any necessary configuration which goes with them. This configuration is represented internally as a dictionary. 
Platform input support configures a `RetrieveResource` object and calls the `run` method triggering the selected steps.
- `RetrieveResource` will consult the steps selected and trigger a method for each selected step. Most steps will defer
to a helper object in `Modules` to retrieve the selected resources.  

# Troubleshooting
```
sudo apt-get install autoconf libtool
```
