import datetime
import logging
import csv
from modules.GoogleSpreadSheet import GoogleSpreadSheet
import json

from definitions import PIS_OUTPUT_TEP, PIS_OUTPUT_ANNOTATIONS

logger = logging.getLogger(__name__)


class TEP(object):

    def __init__(self, output_dir=PIS_OUTPUT_ANNOTATIONS, input_dir=PIS_OUTPUT_TEP):
        self.filename_tep = input_dir + "/tep.tsv"
        self.output_dir = output_dir
        self.input_dir = input_dir
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')

    def download_spreadsheet(self, yaml_dict, safety_output_dir):
        for spreadsheet_info in yaml_dict.spreadsheets:
            google_spreadsheet = GoogleSpreadSheet(safety_output_dir)
            google_spreadsheet.download_as_csv(spreadsheet_info)

    def generate_tep_json(self, yaml_dict):

        output_filename = self.output_dir + '/' + yaml_dict.output_filename.replace('{suffix}', self.suffix)
        tep_json_file = open(output_filename, 'w')
        fieldnames = ("OT_Target_name", "Ensembl_id","URI")

        with open(self.filename_tep, 'rb') as f:
            reader = csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            for i, row in enumerate(reader, start=1):
                tep_entry = dict()
                for key, value in row.items():
                    if key in fieldnames:
                        tep_entry[key]=value
                json.dump(tep_entry, tep_json_file)
                tep_json_file.write('\n')


        #for row in csv.DictReader(self.filename_tep, delimiter='\t', quoting=csv.QUOTE_NONE):
        #    print(row)
        #    json.dump(row, tep_json_file)
        #    tep_json_file.write('\n')

        logger.info("TEP output filename : %s", output_filename)
        return output_filename

