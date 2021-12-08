import logging
from definitions import *
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from modules.common.Utils import Utils
from modules.common import create_output_dir
from modules.common.Riot import Riot
logger = logging.getLogger(__name__)

"""

"""
class SO(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf):
        riot = Riot(cmd_conf)
        filename_input = Downloads.dowload_staging_http(output.staging_dir, conf.etl)
        file_ouput_path = os.path.join(output.prod_dir, conf.etl.path)
        create_output_dir(file_ouput_path)
        riot.convert_owl_to_jsonld(filename_input, file_ouput_path, conf.etl.owl_jq)

