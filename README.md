# platform-input-support
Open Targets Platform input support project.

# Conda for MAC
For Mac goes here: <br>
 https://www.anaconda.com/download/#macos. <br>
 and download Version 2.7 Command-Line Installer

Run  
```
bash ~/Downloads/Anaconda2-5.3.0-MacOSX-x86_64.sh
source ~/.bashrc
conda update
```
The last command ... path/anaconda2
```
conda update --prefix path/anaconda2 anaconda
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
python platform-input-support.py -h
```

# Google Bucket example
```
python platform-input-support.py -gkey /path/open-targets-gac.json -gb ot-snapshots/es5-sufentanil/tmp

python platform-input-support.py 
         --google_credential_key /path/open-targets-gac.json 
         --google_bucket ot-snapshots/es5-sufentanil/tmp
```



```
python -m modules.RetrieveEvidences --skip 
  
python -m modules.RetrieveAnnotations -gkey path/open-targets-gac.json --google_bucket ot-snapshots/es5-sufentanil -step chemical_probes
```

### Use VM such as Google Cloud or Amazon Azure

```
sudo apt update
sudo apt install git
sudo apt-get install bzip2 
```
```
wget https://repo.anaconda.com/archive/Anaconda2-2018.12-Linux-x86_64.sh
bash Anaconda2-2018.12-Linux-x86_64.sh
source ~/.bashrc
conda update --prefix /home/cinzia/anaconda2 anaconda
```

```
mkdir gitRepo
cd gitRepo
git clone https://github.com/opentargets/platform-input-support.git
cd platform-input-support
conda env create -f environment.yaml
conda activate platform-input-support-py2.7
conda install pip
pip install -r requirements.txt
python platform-input-support.py -l
```

Use nohup

```nohup python platform-input-support.py [options] &```