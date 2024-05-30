import datetime
import json
import logging
import os

import jsonlines
from opentargets_urlzsource import URLZSource
from yapsy.IPlugin import IPlugin

from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service
from platform_input_support.modules.common import create_folder, make_gzip, make_unzip_single_file
from platform_input_support.modules.common.downloads import Downloads

logger = logging.getLogger(__name__)


class Expression(IPlugin):
    """Expression data collection step."""

    def __init__(self):
        """Expression class constructor."""
        self._logger = logging.getLogger(__name__)
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.step_name = 'Expression'

    def save_tissue_translation_map(self, output_path, resource, download_manifest) -> ManifestResource:
        """Persist tissue translation map information.

        :param output_path: destination path
        :param resource: resource information object on the persisting data
        :param filename: source file
        """
        if download_manifest.status_completion != ManifestStatus.FAILED:
            tissues_json = {}
            try:
                with URLZSource(download_manifest.path_destination).open(mode='rb') as r_file:
                    tissues_json['tissues'] = json.load(r_file)['tissues']
                # NOTE The following should have been performed by the context handler when exiting the 'with' block
                # r_file.close()
            except Exception as e:
                download_manifest.status_completion = ManifestStatus.FAILED
                download_manifest.msg_completion = (
                    f'COULD NOT extract tissue mapping data'
                    f" from file '{download_manifest.path_destination}',"
                    f" due to '{e}'"
                )
            else:
                path_folder = os.path.join(output_path, resource.path)
                create_folder(path_folder)
                path_filename_tissue = os.path.join(
                    path_folder, resource.output_filename.replace('{suffix}', self.suffix)
                )
                try:
                    with jsonlines.open(path_filename_tissue, mode='w') as writer:
                        for item in tissues_json['tissues']:
                            entry = dict(tissues_json['tissues'][item].items())
                            entry['tissue_id'] = item
                            writer.write(entry)
                except Exception as e:
                    download_manifest.status_completion = ManifestStatus.FAILED
                    download_manifest.msg_completion = (
                        f'COULD NOT persist tissue mapping data'
                        f" to file '{download_manifest.path_destination}',"
                        f" due to '{e}'"
                    )
                else:
                    download_manifest.path_destination = path_filename_tissue
                    self._logger.debug(
                        'Tissue translation map download manifest destination path set to %s, '
                        'which is the destination for the extracted tissue translation data',
                        download_manifest.path_destination,
                    )
                    download_manifest.msg_completion = (
                        'The destination file contains the tissue translation map extracted from the data source'
                    )
                    download_manifest.status_completion = ManifestStatus.COMPLETED
        else:
            self._logger.error(
                'COULD NOT produce tissue translation mapping data, because data file at %s could not be retrieved',
                download_manifest.source_url,
            )
        return download_manifest

    def get_tissue_map(self, output, resource) -> ManifestResource:
        """Collect and persist tissue map information.

        :param output: output folder information
        :param resource: download resource information object
        """
        return self.save_tissue_translation_map(
            output.prod_dir, resource, Downloads.download_staging_http(output.staging_dir, resource)
        )

    def get_normal_tissues(self, output, resource) -> ManifestResource:
        """Collect normal tissue data, gzip compressed.

        :param output: output folder information object
        :param resource: download resource information object
        """
        self._logger.debug('[START] Normal tissue download')
        download_manifest = Downloads.download_staging_http(output.staging_dir, resource)
        if download_manifest.status_completion == ManifestStatus.COMPLETED:
            try:
                filename_unzip = make_unzip_single_file(download_manifest.path_destination)
            except Exception as e:
                download_manifest.status_completion = ManifestStatus.FAILED
                download_manifest.msg_completion = (
                    f'COULD NOT extract normal tissue data'
                    f" from '{download_manifest.path_destination}'"
                    f" due to '{e}'"
                )
                self._logger.error(download_manifest.msg_completion)
            else:
                self._logger.debug('[NORMAL_TISSUE] Filename unzip - %s', filename_unzip)
                gzip_filename = os.path.join(
                    create_folder(os.path.join(output.prod_dir, resource.path)),
                    resource.output_filename.replace('{suffix}', self.suffix),
                )
                self._logger.debug('[NORMAL_TISSUE] Filename gzip - %s', gzip_filename)
                try:
                    download_manifest.path_destination = make_gzip(filename_unzip, gzip_filename)
                except Exception as e:
                    download_manifest.status_completion = ManifestStatus.FAILED
                    download_manifest.msg_completion = (
                        f'COULD NOT gzip normal tissue data'
                        f" from '{filename_unzip}'"
                        f" to '{gzip_filename}'"
                        f" due to '{e}'"
                    )
                    self._logger.error(download_manifest.msg_completion)
                else:
                    self._logger.debug(
                        'Normal tissue data download manifest destination path set to %s, '
                        'which is the result of compression format conversion from original file',
                        download_manifest.path_destination,
                    )
                    download_manifest.msg_completion = (
                        'The source file was converted from its original compression format to gzip format'
                    )
                    download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def process(self, conf, output, cmd_conf=None):
        """Expression data collection pipeline step implementation.

        :param conf: step configuration object
        :param output: output folder information
        :param cmd_conf: NOT USED
        """
        self._logger.info('[STEP] BEGIN, Expression')
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        # TODO - Should I halt the step as soon as I face the first problem?
        manifest_step.resources.append(self.get_tissue_map(output, conf.etl.tissue_translation_map))
        manifest_step.resources.append(self.get_normal_tissues(output, conf.etl.normal_tissues))
        get_manifest_service().compute_checksums(manifest_step.resources)
        if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = 'COULD NOT retrieve all the resources'
        # TODO - Validation
        if manifest_step.status_completion != ManifestStatus.FAILED:
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = 'The step has completed its execution'
        self._logger.info('[STEP] END, Expression')
