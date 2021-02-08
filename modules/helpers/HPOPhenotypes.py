import logging
import datetime
import re
import json
import jsonlines
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS
from ..common import replace_suffix

logger = logging.getLogger(__name__)

class HPOPhenotypes(object):

    def __init__(self, hpo_input):
        self.hpo_phenotypes_input = hpo_input
        self.hpo_phenotypes = []

    def replace_HP_id(self, value):
        return value.replace("HP:", "HP_")


    def convert_string_to_set(self, value, convert_HP_term):
        if self.empty_string_to_null(value) != None:
            if convert_HP_term:
                new_values = []
                values = set(value.split(";"))
                for entry in values:
                    new_values.append(self.replace_HP_id(entry))
                return new_values
            else:
                return list(set(value.split(";")))
        else:
            return None

    def empty_string_to_null(self, value, convert_HP_term=False):
        if value is not None:
            if value == "":
                return None
            else:
                if convert_HP_term:
                    return self.replace_HP_id(value)
                else:
                    return value
        else:
            return None

    def run(self, filename):
        hpo_filename=PIS_OUTPUT_ANNOTATIONS + "/" + replace_suffix(filename)
        with jsonlines.open(hpo_filename, mode='w') as writer:
            with open(self.hpo_phenotypes_input) as input:
                for line in input:
                    if line[0] != '#':
                        data = {}
                        row = line.split('\t')
                        data['databaseId'] = row[0]
                        data['diseaseName'] = row[1]
                        data['qualifier'] = self.empty_string_to_null(row[2])
                        data['HPOId'] = row[3]
                        data['references'] = self.convert_string_to_set(row[4], False)
                        data['evidenceType'] = row[5]
                        data['onset'] = self.convert_string_to_set(row[6], True)
                        data['frequency'] = self.empty_string_to_null(row[7], True)
                        data['sex'] = self.empty_string_to_null(row[8])
                        data['modifiers'] = self.convert_string_to_set(row[9],True)
                        data['aspect'] = row[10]
                        data['biocuration'] = row[11].rstrip()
                        data['resource'] = 'HPO'
                        writer.write(data)

        return hpo_filename
