import logging
import os

from addict import Dict
from yapsy.IPlugin import IPlugin

from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service
from platform_input_support.modules.common import (
    create_folder,
    extract_file_from_zip,
    make_gunzip,
    make_gzip,
    make_unzip_single_file,
)
from platform_input_support.modules.common.downloads import Downloads
from platform_input_support.modules.common.utils import CustomSubProcException, Utils, subproc

logger = logging.getLogger(__name__)


class Target(IPlugin):
    """Target data collection step."""

    def __init__(self):
        """Target class constructor."""
        self._logger = logging.getLogger(__name__)
        self.step_name = 'Target'

    def get_gnomad(self, gnomad, output) -> ManifestResource:
        """Collect gnomeAD data.

        :param gnomad: data source configuration object
        :param output: output configuration object for collected data
        """
        download_manifest = Downloads.download_staging_http(output.staging_dir, gnomad)
        if download_manifest.status_completion == ManifestStatus.COMPLETED:
            download_manifest.status_completion = ManifestStatus.FAILED
            try:
                filename_unzip = make_gunzip(download_manifest.path_destination)
            except Exception as e:
                download_manifest.msg_completion = (
                    'COULD NOT unzip file %s due to',
                    download_manifest.path_destination,
                    e,
                )
            else:
                gzip_filename = os.path.join(
                    create_folder(os.path.join(output.prod_dir, gnomad.path)), gnomad.output_filename
                )
                try:
                    download_manifest.path_destination = make_gzip(filename_unzip, gzip_filename)
                except Exception as e:
                    download_manifest.msg_completion = (
                        'COULD NOT gzip file %s into %s due to %s',
                        filename_unzip,
                        gzip_filename,
                        e,
                    )
                else:
                    self._logger.debug(
                        'gnomeAD data download manifest destination path set to %s, which is the result of compression '
                        'format conversion from original file',
                        download_manifest.path_destination,
                    )
                    download_manifest.msg_completion = (
                        'The source file was converted from its original compression format to gzip format'
                    )
                    download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def get_subcellular_location(self, sub_location, output) -> ManifestResource:
        """Collect subcellular location data.

        :param sub_location: subcellular location data source information object
        :param output: output configuration object for the collected data
        """
        download_manifest = Downloads.download_staging_http(output.staging_dir, sub_location)
        if download_manifest.status_completion == ManifestStatus.COMPLETED:
            download_manifest.status_completion = ManifestStatus.FAILED
            try:
                filename_unzip = make_unzip_single_file(download_manifest.path_destination)
            except Exception as e:
                download_manifest.msg_completion = f'COULD NOT unzip {download_manifest.path_destination} due to {e}'

            else:
                gzip_filename = os.path.join(
                    create_folder(os.path.join(output.prod_dir, sub_location.path)), sub_location.output_filename
                )
                try:
                    download_manifest.path_destination = make_gzip(filename_unzip, gzip_filename)
                except Exception as e:
                    download_manifest.msg_completion = (
                        f'COULD NOT gzip {filename_unzip} into {gzip_filename} due to {e}'
                    )
                else:
                    self._logger.debug(
                        'Subcellular location data download manifest destination path set to %s, '
                        'which is the result of compression format conversion from original file',
                        download_manifest.path_destination,
                    )
                    download_manifest.msg_completion = (
                        'The source file was converted from its original compression format to gzip format'
                    )
                    download_manifest.status_completion = ManifestStatus.COMPLETED
        if download_manifest.status_completion == ManifestStatus.FAILED:
            self._logger.error(download_manifest.msg_completion)
        return download_manifest

    def extract_ensembl(self, ensembl, output, cmd) -> ManifestResource:
        """Collect Ensembl data.

        :param ensembl: ensembl data source configuration object
        :param output: output information object for where to place results
        :param cmd: command line tools configuration object
        """
        logger.info('Converting Ensembl json file into jsonl.')
        jq_cmd = Utils.check_path_command('jq', cmd.jq)
        resource_stage = Dict()
        resource_stage.uri = ensembl.uri.replace('{release}', str(ensembl.release))
        download_manifest = Downloads.download_staging_ftp(output.staging_dir, resource_stage)
        if download_manifest.status_completion == ManifestStatus.COMPLETED:
            output_dir = os.path.join(output.prod_dir, ensembl.path)
            output_file = os.path.join(create_folder(output_dir), ensembl.output_filename)
            cmd = f"{jq_cmd} -c '{ensembl.jq}' {download_manifest.path_destination} > {output_file}"
            try:
                subproc(cmd)
            except CustomSubProcException as e:
                download_manifest.status_completion = ManifestStatus.FAILED
                download_manifest.msg_completion = (
                    f'FAILED to extract ensembl data from'
                    f" '{download_manifest.path_destination}'"
                    f" into '{output_file}'"
                    f" using JQ filter '{ensembl.jq}'"
                    f" due to '{e}'"
                )
                self._logger.error(download_manifest.msg_completion)
            else:
                download_manifest.path_destination = output_file
                self._logger.debug(
                    'Ensembl data extraction download manifest destination path set to %s, '
                    'which is the result of processing the original data source',
                    download_manifest.path_destination,
                )
                download_manifest.msg_completion = (
                    f'The following jq filter has been used for ensembl data extraction: {ensembl.jq}'
                )
                download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def get_project_scores(self, project_score_entry, output) -> ManifestResource:
        """Download project scoring information.

        :param project_score_entry: project scoring data download information
        :param output: output configuration object for download
        """
        # we only want one file from a zipped archive
        file_of_interest = 'EssentialityMatrices/04_binaryDepScores.tsv'
        download_manifest = Downloads.download_staging_http(output.staging_dir, project_score_entry)
        if download_manifest.status_completion == ManifestStatus.COMPLETED:
            output_dir = os.path.join(output.prod_dir, project_score_entry.path)
            create_folder(output_dir)
            try:
                extract_file_from_zip(file_of_interest, download_manifest.path_destination, output_dir)
            except Exception as e:
                download_manifest.status_completion = ManifestStatus.FAILED
                download_manifest.msg_completion = (
                    f"FAILED to extract '{file_of_interest}'"
                    f" from '{download_manifest.path_destination}' due to '{e}'"
                )
            else:
                download_manifest.path_destination = os.path.join(output_dir, os.path.basename(file_of_interest))
                self._logger.debug(
                    'Project Score download manifest destination path set to %s', download_manifest.path_destination
                )
                download_manifest.msg_completion = f"From within original file, '{file_of_interest}' was the one used"
                download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def process(self, conf, output, cmd_conf):
        """Target data collection pipeline step implementation.

        :param conf: step configuration object
        :param output: output configuration object for step results
        :param cmd_conf: command line tools configuration object
        """
        self._logger.info('[STEP] BEGIN, target')
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        # TODO - Should I halt the step as soon as I face the first problem?
        manifest_step.resources.append(self.get_project_scores(conf.etl.project_scores, output))
        manifest_step.resources.append(self.extract_ensembl(conf.etl.ensembl, output, cmd_conf))
        manifest_step.resources.append(self.get_subcellular_location(conf.etl.subcellular_location, output))
        manifest_step.resources.append(self.get_gnomad(conf.etl.gnomad, output))
        get_manifest_service().compute_checksums(manifest_step.resources)
        if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = 'COULD NOT retrieve all the resources'
        # TODO - Validation
        if manifest_step.status_completion != ManifestStatus.FAILED:
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = 'The step has completed its execution'
        self._logger.info('[STEP] END, target')
