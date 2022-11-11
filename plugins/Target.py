import os
import logging
import subprocess
from addict import Dict
from yapsy.IPlugin import IPlugin
from modules.common.Utils import Utils
from modules.common.Downloads import Downloads
from manifest import ManifestResource, ManifestStatus, get_manifest_service
from modules.common import extract_file_from_zip, create_folder, make_gunzip, make_gzip, make_unzip_single_file

logger = logging.getLogger(__name__)


class Target(IPlugin):
    """
    Target pipeline step
    """

    def __init__(self):
        """
        Constructor, prepare logging subsystem
        """
        self._logger = logging.getLogger(__name__)
        self.step_name = "Target"

    def get_gnomad(self, gnomad, output) -> ManifestResource:
        """
        Collect gnomeAD data

        :param gnomad: data source configuration object
        :param output: output configuration object for collected data
        """
        download_manifest = Downloads.download_staging_http(output.staging_dir, gnomad)
        filename_unzip = make_gunzip(download_manifest.path_destination)
        gzip_filename = os.path.join(create_folder(os.path.join(output.prod_dir, gnomad.path)), gnomad.output_filename)
        download_manifest.path_destination = make_gzip(filename_unzip, gzip_filename)
        self._logger.debug(
            f"gnomeAD data download manifest destination path"
            f" set to '{download_manifest.path_destination}',"
            f" which is the result of compression format conversion from original file"
        )
        download_manifest.msg_completion = \
            "The source file was converted from its original compression format to gzip format"
        download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def get_subcellular_location(self, sub_location, output) -> ManifestResource:
        """
        Collect subsellular location data

        :param sub_location: subcellular location data source information object
        :param output: output configuration object for the collected data
        """
        download_manifest = Downloads.download_staging_http(output.staging_dir, sub_location)
        # TODO - Handle possible download errors
        filename_unzip = make_unzip_single_file(download_manifest.path_destination)
        gzip_filename = os.path.join(create_folder(os.path.join(output.prod_dir, sub_location.path)),
                                     sub_location.output_filename)
        # TODO - Handle possible errors when unzipping / gzipping the file
        download_manifest.path_destination = make_gzip(filename_unzip, gzip_filename)
        self._logger.debug(
            f"Subcellular location data download manifest destination path"
            f" set to '{download_manifest.path_destination}',"
            f" which is the result of compression format conversion from original file"
        )
        download_manifest.msg_completion = \
            "The source file was converted from its original compression format to gzip format"
        download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def extract_ensembl(self, ensembl, output, cmd) -> ManifestResource:
        """
        Collect Ensembl data

        :param ensembl: ensembl data source configuration object
        :param output: output information object for where to place results
        :param cmd: command line tools configuration object
        """
        logger.info("Converting Ensembl json file into jsonl.")
        jq_cmd = Utils.check_path_command("jq", cmd.jq)
        resource_stage = Dict()
        resource_stage.uri = ensembl.uri.replace('{release}', str(ensembl.release))
        download_manifest = Downloads.download_staging_ftp(output.staging_dir, resource_stage)
        # TODO - Check whether the download was completed or not
        output_dir = os.path.join(output.prod_dir, ensembl.path)
        output_file = os.path.join(create_folder(output_dir), ensembl.output_filename)
        with open(output_file, "wb") as jsonwrite:
            # TODO - Change this to subprocess.run, and modify the command to write the data straight away, instead of
            #  piping it back to the caller
            jqp = subprocess.Popen(
                [jq_cmd, "-c", ensembl.jq, download_manifest.path_destination],
                stdout=subprocess.PIPE)
            jsonwrite.write(jqp.stdout.read())
        download_manifest.path_destination = output_file
        self._logger.debug(
            f"Ensembl data extraction download manifest destination path set to '{download_manifest.path_destination}',"
            f" which is the result of processing the original data source"
        )
        download_manifest.msg_completion = f"The following 'jq' filter has been used for ensembl data extraction," \
                                           f" '{ensembl.jq}'"
        download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def get_project_scores(self, project_score_entry, output) -> ManifestResource:
        """
        Download project scoring information

        :param project_score_entry: project scoring data download information
        :param output: output configuration object for download
        """
        # we only want one file from a zipped archive
        file_of_interest = 'EssentialityMatrices/04_binaryDepScores.tsv'
        download_manifest = Downloads.download_staging_http(output.staging_dir, project_score_entry)
        # TODO - Check whether the download was completed or not
        output_dir = os.path.join(output.prod_dir, project_score_entry.path)
        create_folder(output_dir)
        extract_file_from_zip(file_of_interest, download_manifest.path_destination, output_dir)
        download_manifest.path_destination = os.path.join(output_dir, os.path.basename(file_of_interest))
        self._logger.debug(
            f"Project Score download manifest destination path set to '{download_manifest.path_destination}', "
            f"which is the extracted file of interest"
        )
        download_manifest.msg_completion = f"From original file, '{file_of_interest}' was the one used"
        download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def process(self, conf, output, cmd_conf):
        """
        Target data collection pipeline step implementation

        :param conf: step configuration object
        :param output: output configuration object for step results
        :param cmd_conf: command line tools configuration object
        """
        self._logger.info("[STEP] BEGIN, target")
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        manifest_step.resources.append(self.get_project_scores(conf.etl.project_scores, output))
        manifest_step.resources.append(self.extract_ensembl(conf.etl.ensembl, output, cmd_conf))
        manifest_step.resources.append(self.get_subcellular_location(conf.etl.subcellular_location, output))
        manifest_step.resources.append(self.get_gnomad(conf.etl.gnomad, output))
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, target")
