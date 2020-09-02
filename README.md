# Open Targets: Platform-input-support overview
The aim of this application is to allow the reproducibility of OpenTarget Platform data release pipeline.
The input files are copied in a specific google storage bucket.

Currently, the application executes 6 steps and finally it generates a Yaml config file that can be used to run the
the OT pipeline (https://github.com/opentargets/data_pipeline)

List of available steps:
- annotations
- annotations from buckets
- chemical probes
- known target safety
- ensembl
- ChEMBL
- evidences
- networks

The step 'evidences' uploads the last evidences from different providers and it generates a subset of these evidences using the file minimal_ensembl.txt

Below more details about how to execute the script.

# Installation Requirements
* Conda
* git

## Conda for MAC
Download Conda for Mac here: <br>
 https://www.anaconda.com/download/#macos. <br>
[download Version 2.7 Command-Line Installer]

Conda: installation commands
```
bash path_where_downloaded_the_file/Anaconda2-5.3.0-MacOSX-x86_64.sh
source ~/.bashrc
conda update
conda update --prefix  ~/anaconda2 anaconda
```

# Set up application (first time)
```
git clone https://github.com/opentargets/platform-input-support
cd platform-input-support
conda env create -f environment.yaml
conda activate platform-input-support-py2.7
conda skeleton pypi opentargets-urlzsource
conda build opentargets-urlzsource
conda build purge
conda install -y --use-local opentargets-urlzsource

python platform-input-support.py -h
```

## Usage

```
conda activate platform-input-support-py2.7
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
         -steps annotations evidences
         -exclude ChEMBL
or
python platform-input-support.py
         -gkey /path/open-targets-gac.json
         -gb bucket/object_path -steps ChEMBL
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
wget https://repo.anaconda.com/archive/Anaconda2-2019.10-Linux-x86_64.sh
bash Anaconda2-2019.10-Linux-x86_64.sh
source ~/.bashrc
conda update --prefix ~/anaconda2 anaconda
```

```
mkdir gitRepo
cd gitRepo
git clone https://github.com/opentargets/platform-input-support.git
cd platform-input-support
conda env create -f environment.yaml
conda activate platform-input-support-py2.7
conda skeleton pypi opentargets-urlzsource
conda build opentargets-urlzsource
conda build purge
conda install -y --use-local opentargets-urlzsource
python platform-input-support.py -l
```

Use nohup to avoid that the process hang up.

```nohup python platform-input-support.py [options] &

Eg.
nohup python platform-input-support.py
         -gkey /path/open-targets-gac.json
         -gb bucket/object_path -steps ChEMBL
         --log-level DEBUG > log.txt &
```

# Application architecture

- `platform-input-support` is the entrypoint to the program; it loads the `config.yaml` which specifies the available
steps and any necessary configuration which goes with them. This configuration is represented internally as a dictionary. 
Platform input support configures a `RetrieveResource` object and calls the `run` method triggering the selected steps.
- `RetrieveResource` will consult the steps selected and trigger a method for each selected step. Most steps will defer
to a helper object in `Modules` to retrieve the selected resources.  

# Troubleshooting

## Installation

### Conda can't find 'opentargets-urlzsource'

The `opentargets-urlzsource` package needs to be build manually. For some reason conda 4.8.4 gives a `PackageNotFoundError   
when the following command is executed:

```
conda install -y --use-local opentargets-urlzsource
```

To solve this problem install the package from the 'base' environment with the following command, updated as necessary for
the location of you miniconda installation.

```bash
conda install --name platform-input-support-py2.7 -c file:///[path to miniconda]/envs/platform-input-support-py2.7/conda-bld/linux-64/ opentargets-urlzsource
```

