import logging
import jsonlines
from platform_input_support.modules.common import set_suffix_timestamp

logger = logging.getLogger(__name__)


class HPOPhenotypesException(Exception):
    pass


class HPOPhenotypes(object):

    def __init__(self, hpo_input):
        """
        Constructor

        :param hpo_input: HPO input data file
        """
        self.hpo_phenotypes_input = hpo_input

    def replace_HP_id(self, value):
        """
        Normalise IDs, 'HP:' to 'HP_'

        :param value: ID to normalise
        :return: normalised ID
        """
        return value.replace("HP:", "HP_")

    def convert_string_to_set(self, value, convert_HP_term):
        """
        Convert a string to a set by splitting on ';', optionally normalising the term IDs

        :param value: string to convert
        :param convert_HP_term: whether or not each HP term in the string should be normalised
        :return: a list of HP terms or None if the string was empty or None
        """
        if self.empty_string_to_null(value) is not None:
            if convert_HP_term:
                return [self.replace_HP_id(entry) for entry in set(value.split(";"))]
            return list(set(value.split(";")))
        return None

    def empty_string_to_null(self, value, convert_HP_term=False):
        """
        Convert empty string to None or return the string, optionally normalised

        :param value: string to convert
        :param convert_HP_term: whether the non-empty string value should be normalised
        """
        if value is not None and value != "":
            if convert_HP_term:
                return self.replace_HP_id(value)
            return value
        return None

    def run(self, filename):
        """
        Convert input HPO Phenotype data into a new data model, persisting it in the given file path.

        :param filename: destination file path with 'suffix' placeholder for the new data model
        :return: file path where the new data model has been persisted
        """
        # WARNING - This helper should not be changing the output file name
        hpo_filename = set_suffix_timestamp(filename)
        try:
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
                            data['modifiers'] = self.convert_string_to_set(row[9], True)
                            data['aspect'] = row[10]
                            data['biocuration'] = row[11].rstrip()
                            data['resource'] = 'HPO'
                            writer.write(data)
        except Exception as e:
            raise HPOPhenotypesException(
                f"COULD NOT convert HPO Phenotype data model and write to file '{hpo_filename}', due to '{e}'")
        return hpo_filename
