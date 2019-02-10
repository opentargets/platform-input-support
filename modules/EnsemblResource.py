import logging
from definitions import ROOT_DIR, PIS_OUTPUT_ANNOTATIONS
import subprocess
logger = logging.getLogger(__name__)

#
# conda env create -f environment.yaml
# conda activate genetics-backend
# usage: create_genes_dictionary.py [-h] [-o PATH] [-e] [-z]
#                                   [-n ENSEMBL_DATABASE]


class EnsemblResource(object):

    def __init__(self, yaml_dict, output_dir = PIS_OUTPUT_ANNOTATIONS):
        self.conda_env = yaml_dict.conda_env
        self.conda_create = yaml_dict.conda_create
        self.ensembl_release = yaml_dict.ensembl_release
        self.python_script = yaml_dict.python_script
        self.output_dir = output_dir
        self.extension_file = yaml_dict.extension_file

    def is_valid_conda_env(self):
        valid_conda_env = False
        command = 'bash -c "~/anaconda2/bin/conda env list | grep "' + self.conda_env
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait()
        # maybe process.returncode return 1 when grep is empty
        for line in iter(process.stdout.readline, ''):
            valid_conda_env = True
        return valid_conda_env

    def create_conda_env(self):
        logging.info("Creating a new Conda env. This command might require a couple of minutes...")
        command = self.conda_create.replace('{root_dir}', ROOT_DIR)
        logging.debug("Conda command %s", command)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        process.wait()
        logging.info("... done! %s",process.returncode)
        return process.returncode


    def create_genes_dictionary(self):
        # check if conda env exists.
        if not self.is_valid_conda_env():
            logger.info("Conda env %s not available", self.conda_env)
            self.create_conda_env()

        logger.info("Conda env %s is available. Ensembl file generation...", self.conda_env)

        script_path = ROOT_DIR + "/scripts/ensembl"
        python_command = self.python_script.replace('{script_path}', script_path).replace('{ensembl_output_dir}', self.output_dir)
        python_command = python_command + ' ' + self.ensembl_release
        shell_command = 'bash -c "source ~/anaconda2/bin/activate ' + self.conda_env
        shell_command = shell_command+' && '+ python_command + ' && conda deactivate"'
        logging.debug(shell_command)
        process = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE)
        process.wait()
        logger.info("Ensembl filename downloaded: %s", self.ensembl_release+self.extension_file)
        return self.output_dir + '/' + self.ensembl_release+self.extension_file

