import json
import logging
import os
import uuid
import zipfile

from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service
from platform_input_support.modules.common.download_resource import DownloadResource

logger = logging.getLogger(__name__)


class Openfda:
    """OpenFDA data download Helper with re-entrant download event file method for multithreading safety."""

    def __init__(self, output_dir, logger=None, manifest_service=None):
        """OpenFDA helper constructor class.

        :param output_dir: destination folder for the downloaded event file
        """
        self.output = output_dir
        self._logger = logger
        self.__manifest_service = manifest_service

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logger
        return self._logger

    @property
    def manifest_service(self):
        if self.__manifest_service is None:
            self.__manifest_service = get_manifest_service()
        return self.__manifest_service

    def do_download_openfda_event_file(self, download_entry) -> list[ManifestResource]:
        """Download a given OpenFDA event file and uncompress and process its contents.

        :param download_entry: download information object
        """
        self.logger.debug(download_entry)
        download_url = download_entry['file']
        download_description = download_entry['display_name']
        download_dest_filename = f'{uuid.uuid4()}.zip'
        download_dest_path = os.path.join(self.output, download_dest_filename)
        download_resource_key = f'openfda-event-{download_dest_filename}'
        self.logger.info(
            'Download OpenFDA FAERs %s, from %s --> %s', download_description, download_url, download_dest_filename
        )
        download_resource = type(
            'download_resource',
            (object,),
            {
                'uri': download_url,
                'unzip_file': True,
                'resource': download_resource_key,
                'output_filename': download_dest_filename,
                'accept': 'application/zip',
            },
        )
        # Download the file
        download_manifest = DownloadResource(self.output, manifest_service=self.manifest_service).execute_download(
            download_resource, 7
        )
        event_file_manifests = []
        with zipfile.ZipFile(download_dest_path, 'r') as zipf:  # noqa: PLR1702
            for event_file in zipf.filelist:
                unzip_filename = event_file.filename
                unzip_dest_filename = f'{uuid.uuid4()}.jsonl'
                unzip_dest_path = os.path.join(self.output, unzip_dest_filename)
                self.logger.debug('Inflating event file %s, CRC %s', unzip_filename, event_file.CRC)
                event_file_manifest = self.manifest_service.clone_resource(download_manifest)
                event_file_manifest.path_destination = unzip_dest_path
                event_file_manifest.status_completion = (
                    f'Original file name within compressed source file,'
                    f" '{unzip_filename}'. Description: {download_description}"
                )
                wrote_results = False

                with zipf.open(unzip_filename, 'r') as compressedf:
                    with open(unzip_dest_path, 'w') as inflatedf:
                        event_data = json.load(compressedf)
                        if event_data['results']:
                            wrote_results = True
                            for result in event_data['results']:
                                inflatedf.write(f'{format(json.dumps(result))}\n')
                        else:
                            self.logger.warning(
                                'NO EVENT DATA RESULTS for event file %s, source URL %s, description %s',
                                unzip_filename,
                                download_url,
                                download_description,
                            )
                event_file_manifest.status_completion = ManifestStatus.COMPLETED
                if wrote_results:
                    event_file_manifests.append(event_file_manifest)
        self.logger.debug('Removing processed ZIP file: %s', download_dest_path)
        os.remove(download_dest_path)
        return event_file_manifests
