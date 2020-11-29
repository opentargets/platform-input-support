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

    def run(self, filename):
        with jsonlines.open(PIS_OUTPUT_ANNOTATIONS + "/" + replace_suffix(filename), mode='w') as writer:
            with open(self.hpo_phenotypes_input) as input:
                for line in input:
                    if line[0] != '#':
                        data = {}
                        row = line.split('\t')
                        data['databaseId'] = row[0]
                        data['diseaseName'] = row[1]
                        data['qualifier'] = row[2]
                        data['HPOId'] = row[3]
                        data['reference'] = row[4]
                        data['evidence'] = row[5]
                        data['onset'] = row[6]
                        data['frequency'] = row[7]
                        data['sex'] = row[8]
                        data['modifier'] = row[9]
                        data['aspect'] = row[10]
                        data['biocuration'] = row[11].rstrip()
                        writer.write(data)

