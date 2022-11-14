import os
import json
import logging
import datetime
import jsonlines
from yapsy.IPlugin import IPlugin
from modules.common import create_folder
from opentargets_urlzsource import URLZSource
from modules.common.Downloads import Downloads
from modules.common import make_unzip_single_file, make_gzip
from manifest import ManifestResource, ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)


class Expression(IPlugin):
    """
    Expression data collection step implementation
    """

    def __init__(self):
        """
        Constructor, prepare the logging subsystem and a time stamp for the files
        """
        self._logger = logging.getLogger(__name__)
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.step_name = "Expression"

    def save_tissue_translation_map(self, output_path, resource, download_manifest) -> ManifestResource:
        """
        Persist tissue translation map information

        :param output_path: destination path
        :param resource: resource information object on the persisting data
        :param filename: source file
        """
        # TODO - Check whether the download manifest signals completion
        tissues_json = {}
        # TODO - Check for errors happening when processing the file
        with URLZSource(download_manifest.path_destination).open(mode='rb') as r_file:
            tissues_json['tissues'] = json.load(r_file)['tissues']
        # NOTE The following should have been performed by the context handler when exiting the 'with' block
        r_file.close()
        create_folder(os.path.join(output_path, resource.path))
        filename_tissue = os.path.join(output_path, resource.path,
                                       resource.output_filename.replace('{suffix}', self.suffix))
        with jsonlines.open(filename_tissue, mode='w') as writer:
            for item in tissues_json['tissues']:
                entry = {k: v for k, v in tissues_json['tissues'][item].items()}
                entry['tissue_id'] = item
                writer.write(entry)
        download_manifest.path_destination = filename_tissue
        self._logger.debug(
            f"Tissue translation map download manifest destination path set to '{download_manifest.path_destination}', "
            f"which is the destination for the extracted tissue translation data"
        )
        download_manifest.msg_completion = f"The destination file contains the tissue translation map extracted from" \
                                           f" the data source"
        download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def get_tissue_map(self, output, resource) -> ManifestResource:
        """
        Collect and persist tissue map information

        :param output: output folder information
        :param resource: download resource information object
        """
        return self.save_tissue_translation_map(output.prod_dir,
                                         resource,
                                         Downloads.download_staging_http(output.staging_dir, resource))

    def get_normal_tissues(self, output, resource) -> ManifestResource:
        """
        Collect normal tissue data, gzip compressed.

        :param output: output folder information object
        :param resource: download resource information object
        """
        self._logger.debug("[START] Normal tissue download")
        download_manifest = Downloads.download_staging_http(output.staging_dir, resource)
        filename_unzip = make_unzip_single_file(download_manifest.path_destination)
        self._logger.debug(f"[NORMAL_TISSUE] Filename unzip - '{filename_unzip}'")
        gzip_filename = os.path.join(create_folder(os.path.join(output.prod_dir, resource.path)),
                                     resource.output_filename.replace('{suffix}', self.suffix))
        self._logger.debug(f"[NORMAL_TISSUE] Filename gzip - '{gzip_filename}'")
        download_manifest.path_destination = make_gzip(filename_unzip, gzip_filename)
        self._logger.debug(
            f"Normal tissues' data download manifest destination path"
            f" set to '{download_manifest.path_destination}',"
            f" which is the result of compression format conversion from original file"
        )
        download_manifest.msg_completion = \
            "The source file was converted from its original compression format to gzip format"
        download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def process(self, conf, output, cmd_conf=None):
        """
        Expression data collection pipeline step implementation

        :param conf: step configuration object
        :param output: output folder information
        :param cmd_conf: NOT USED
        """
        self._logger.info("[STEP] BEGIN, Expression")
        manifest_step = get_manifest_service().manifest_service.get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        manifest_step.resources.append(self.get_tissue_map(output, conf.etl.tissue_translation_map))
        manifest_step.resources.append(self.get_normal_tissues(output, conf.etl.normal_tissues))
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, Expression")
