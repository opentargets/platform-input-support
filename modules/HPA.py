import datetime
import logging
from .DownloadResource import DownloadResource
from .common import make_unzip_single_file
from opentargets_urlzsource import URLZSource
import jsonlines
import json

from definitions import PIS_OUTPUT_ANNOTATIONS

logger = logging.getLogger(__name__)


class HPA(object):

    def __init__(self, yaml_dict, args):
        self.yaml = yaml_dict
        self.args = args
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.list_files_downloaded = {}


    def elaborate_tissue_translation_map(self, destination_filename):
        tissues_json = {}
        with URLZSource(destination_filename).open(mode='rb') as r_file:
            tissues_json['tissues'] = json.load(r_file)['tissues']
        return tissues_json

    def save_tissue_translation_map(self, filename, tissues_json):
        tissue_filename = filename.replace(".tmp", "")
        with jsonlines.open(tissue_filename, mode='w') as writer:
            for item in tissues_json['tissues']:
                entry = {k: v for k, v in tissues_json['tissues'][item].items()}
                entry['tissue_id'] = item
                writer.write(entry)

        return tissue_filename

    def get_hpa_annonations(self):
        for entry in self.yaml.downloads:
            download = DownloadResource(PIS_OUTPUT_ANNOTATIONS)
            download.replace_suffix(self.args)
            destination_filename = download.execute_download(entry)

            if destination_filename is not None:
                if 'unzip_file' in entry:
                    destination_filename = make_unzip_single_file(destination_filename)

                if entry.resource == "tissue-translation-map":
                    # manipulate file with weird format
                    tissues_json = self.elaborate_tissue_translation_map(destination_filename)
                    destination_filename=self.save_tissue_translation_map(destination_filename,tissues_json)

                self.list_files_downloaded[destination_filename] = { 'resource' : entry.resource,
                                                                     'gs_output_dir': self.yaml.gs_output_dir }
                logger.info("Files downloaded: %s", destination_filename)
            elif not self.args.skip:
                 raise ValueError("Error during downloading: {}", entry.uri)

        logger.info("Number of resources requested / Number of files downloaded: %s / %s",
                    len(self.yaml.downloads), len(self.list_files_downloaded))

        return self.list_files_downloaded

