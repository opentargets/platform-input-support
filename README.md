# platform-input-support
Open Targets Platform input support project.


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
