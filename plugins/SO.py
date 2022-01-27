import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from modules.common import create_folder
from modules.common.Riot import Riot
import os

logger = logging.getLogger(__name__)


"""

"""


class SO(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf):
        riot = Riot(cmd_conf)
        filename_input = Downloads.download_staging_http(output.staging_dir, conf.etl)
        file_ouput_path = os.path.join(output.prod_dir, conf.etl.path)
        create_folder(file_ouput_path)
        riot.convert_owl_to_jsonld(filename_input, file_ouput_path, conf.etl.owl_jq)
