import os
import json
import uuid
import logging
import zipfile
from urllib.parse import urlparse
from modules.common.DownloadResource import DownloadResource

logger = logging.getLogger(__name__)


class OpenfdaHelper(object):
    """
    OpenFDA data download Helper with re-entrant download event file method for multithreading safety.
    """

    def __init__(self, output_dir):
        """
        Constructor

        :param output_dir: destination folder for the downloaded event file
        """
        self.output = output_dir

    def _do_download_openfda_event_file(self, download_entry):
        """
        Download a given OpenFDA event file and uncompress and process its contents to their final destination file path

        :param download_entry: download information object
        """
        logger.info(download_entry)
        download_url = download_entry['file']
        download_description = download_entry['display_name']
        download_src_filename = os.path.basename(urlparse(download_url).path)
        download_dest_filename = "{}.zip".format(uuid.uuid4())
        download_dest_path = os.path.join(self.output, download_dest_filename)
        download_resource_key = "openfda-event-{}".format(download_dest_filename)
        logger.info("Download OpenFDA FAERs '{}', from '{}', destination file name '{}'".format(download_description,
                                                                                                download_url,
                                                                                                download_src_filename))
        download_resource = type('download_resource', (object,), {
            'uri': download_url,
            'unzip_file': True,
            'resource': download_resource_key,
            'output_filename': download_dest_filename,
            'accept': 'application/zip'
        })
        # Download the file
        DownloadResource(self.output) \
            .execute_download(download_resource, 7)
        with zipfile.ZipFile(download_dest_path, 'r') as zipf:
            for event_file in zipf.filelist:
                unzip_filename = event_file.filename
                unzip_dest_filename = "{}.jsonl".format(uuid.uuid4())
                unzip_dest_path = os.path.join(self.output, unzip_dest_filename)
                logger.debug("Inflating event file '{}', CRC '{}'".format(unzip_filename, event_file.CRC))
                with zipf.open(unzip_filename, 'r') as compressedf:
                    with open(unzip_dest_path, 'w') as inflatedf:
                        logger.debug("Extracting event file results")
                        event_data = json.load(compressedf)
                        if event_data['results']:
                            for result in event_data['results']:
                                inflatedf.write("{}\n".format(json.dumps(result)))
                        else:
                            logger.warning(
                                "NO EVENT DATA RESULTS for event file '{}', source URL '{}', description '{}'".format(
                                    unzip_filename, download_url, download_description))
        logger.warning("Removing processed ZIP file '{}'".format(download_dest_path))
        os.remove(download_dest_path)


if __name__ == '__main__':
    pass
