# platform-input-support
Open Targets Platform input support project.

# Conda for MAC
For Mac goes here: <br>
 https://www.anaconda.com/download/#macos. <br>
 and download Version 2.7 Command-Line Installer

Run  
```
bash ~/Downloads/Anaconda2-5.3.0-MacOSX-x86_64.sh
```

# Installation
```
conda env create -f environment.yaml
conda activate platform-input-support-py2.7
conda install pip
pip install -r requirements.txt
```

## Usage

```
usage: python platform-input-support.py [-h] [-c CONFIG] [-o OUTPUT_DIR]
                                 [-i INPUT_FILE] [-t] [-s SUFFIX]

...

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to config file (YAML) [env var: CONFIG] (default:
                        None)
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        By default, the files are generated in the root
                        directory [env var: OT_OUTPUT_DIR] (default: None)
  -i INPUT_FILE, --input_file INPUT_FILE
                        By default the file ROOT_DIR/annotations_input.csv
                        will be loaded [env var: OT_INPUT_FILE] (default:
                        None)
  -t, --thread          Run the script with thread [env var: OT_THREAD]
                        (default: False)
  -s SUFFIX, --suffix SUFFIX
                        The default suffix is yyyy-mm-dd [env var:
                        OT_SUFFIX_INPUT] (default: None)
```

## Alternative Usage example

```
python -m modules.RetrieveAnnotations -h
```
or
```
cd modules
python -m RetrieveAnnotations -h
```

# Google Bucket example
```
python platform-input-support.py -gkey /path/open-targets-gac.json -gb ot-snapshots/es5-sufentanil/tmp

python platform-input-support.py 
         --google_credential_key /path/open-targets-gac.json 
         --google_bucket ot-snapshots/es5-sufentanil/tmp
```

```
python -m modules.RetrieveAnnotations  \ 
       -gkey /Users/cinzia/gitRepositories/platform-input-support/open-targets-gac.json \ 
       --google_bucket ot-snapshots/es5-sufentanil/tmp/19.02/input/annotation-files
```


```
python -m modules.RetrieveEvidences -gkey /Users/cinzia/gitRepositories/platform-input-support/open-targets-gac.json

python -m modules.RetrieveEvidences --skip  \ 
       -gkey /Users/cinzia/gitRepositories/platform-input-support/open-targets-gac.json

python -m modules.RetrieveEvidences --skip  \ 
       -gkey /Users/cinzia/gitRepositories/platform-input-support/open-targets-gac.json  \ 
       -gb ot-snapshots/es5-sufentanil/tmp/19.02/input/evidence-files
  
python -m modules.RetrieveAnnotations -gkey /Users/cinzia/gitRepositories/platform-input-support/open-targets-gac.json --google_bucket ot-snapshots/es5-sufentanil -step chemical_probes
```