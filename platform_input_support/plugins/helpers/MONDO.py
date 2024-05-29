import re
import json
import logging
import jsonlines

logger = logging.getLogger(__name__)


class MONDOException(Exception):
    pass


class MONDO(object):

    def __init__(self, mondo_input):
        """
        Constructor for the MONDO data model instance

        :param mondo_input: input file path
        """
        self.mondo_input = mondo_input
        self.mondo = {}

    def init_mondo(self, id):
        """
        Initialise a term entry given the term ID, in the current MONDO data model instance

        :param id: term ID
        """
        self.mondo[id] = {}
        self.mondo[id]['id'] = id
        self.mondo[id]['resource'] = 'MONDO'

    def extract_id(self, elem):
        """
        Given a term, this method 'normalises' the ID by replacing ':' for '_'

        :param elem: term to normalise
        :return: the normalised ID
        """
        return elem.replace(":", "_")

    def get_id(self, mondo):
        """
        Extract term ID from the given MONDO term or skip it in case it contains no ID

        :param mondo: term to extract ID from
        :return: the extracted ID, None otherwise
        """
        if 'id' in mondo:
            return mondo['id'].replace(":", "_")
        if '@id' in mondo:
            return re.sub(r'^.*?:', '', mondo['@id'])
        else:
            # NOTE WHAAAAT? hahaha!
            logger.warning(
                "WTF just happened here? - neither 'id' nor '@id' has been found in this MONDO item: '{}'".format(
                    mondo))

    def set_dbXRefs(self, id, mondo):
        """
        Compute DB Xrefs for the given term ID according to the given MONDO information object, in the current MONDO
        data model instance

        :param id: term ID
        :param mondo: MONDO information object
        """
        dbXRefs = []
        if 'hasDbXref' in mondo:
            if isinstance(mondo['hasDbXref'], str):
                dbXRefs.append(mondo['hasDbXref'])
            else:
                for ref in mondo['hasDbXref']:
                    dbXRefs.append(ref)

            self.mondo[id]['dbXRefs'] = dbXRefs

    def set_obsoleted_term(self, id, mondo):
        """
        Compute obsolete terms information for the given term ID, according to the given MONDO information object in the
        current MONDO data model instance

        :param id: term ID
        :param mondo: MONDO information object
        """
        if "hasAlternativeId" in mondo:
            obsolete = []
            if isinstance(mondo['hasAlternativeId'], str):
                obsolete.append(self.extract_id(mondo['hasAlternativeId']))
            else:
                for term in mondo['hasAlternativeId']:
                    obsolete.append(self.extract_id(term))

            self.mondo[id]['obsolete_terms'] = obsolete

    def set_label(self, id, mondo):
        """
        Set the MONDO label information for the given term ID in the current MONDO data model instance

        :param id: term ID
        :param mondo: MONDO information object
        """
        if 'label' in mondo:
            if isinstance(mondo['label'], str):
                self.mondo[id]['name'] = mondo['label']
            elif isinstance(mondo['label'], dict):
                self.mondo[id]['name'] = mondo['label']['@value']
            else:
                if isinstance(mondo['label'][0], str):
                    self.mondo[id]['name'] = mondo['label'][0]
                else:
                    self.mondo[id]['name'] = mondo['label'][0]['@value']

    def is_valid(self, mondo):
        """
        Check wheter the given MONDO information object describes a NOT deprecated term or not.

        :return: False if the given MONDO term is deprecated, True otherwise
        """
        return 'owl:deprecated' not in mondo

    def get_subClassOf(self, id, mondo):
        """
        Compute the superclasses for the given term ID according to the information in the given MONDO object for the
        current MONDO data model instance

        :param id: term ID
        :param mondo: MONDO information object
        """
        if "subClassOf" in mondo:
            classesOf = []
            if isinstance(mondo['subClassOf'], str):
                classesOf.append(re.sub(r'^.*?:', '', mondo['subClassOf']).replace(":", "_"))
            else:
                for term in mondo['subClassOf']:
                    classesOf.append(re.sub(r'^.*?:', '', term).replace(":", "_"))

            self.mondo[id]['subClassOf'] = classesOf

    def set_mapping(self, id, mondo):
        """
        Set mapping information for the given term ID according to the provided MONDO information object in the current
        MONDO data model instance

        :param id: term ID
        :param mondo: MONDO information object
        """
        if 'someValuesFrom' in mondo:
            self.mondo[id]['mapping'] = re.sub(r'^.*?:', '', mondo['someValuesFrom']).replace(":", "_")

    def set_phenotype(self):
        """
        Set phenotype information for the current MONDO data model instance
        """
        for mondo_id in self.mondo:
            phenotypes = []
            if 'subClassOf' in self.mondo[mondo_id]:
                for elem in self.mondo[mondo_id]['subClassOf']:
                    if elem in self.mondo:
                        if 'mapping' in self.mondo[elem]:
                            phenotypes.append(self.mondo[elem]['mapping'])
                        else:
                            phenotypes.append(elem)
            self.mondo[mondo_id]['phenotypes'] = phenotypes

    def generate(self):
        """
        Process MONDO input data and compute the MONDO data model instance
        """
        try:
            with open(self.mondo_input) as input:
                for line in input:
                    mondo = json.loads(line)
                    id = self.get_id(mondo)
                    if self.is_valid(mondo):
                        self.init_mondo(id)
                        self.set_label(id, mondo)
                        self.set_dbXRefs(id, mondo)
                        self.set_obsoleted_term(id, mondo)
                        self.get_subClassOf(id, mondo)
                        self.set_mapping(id, mondo)
        except Exception as e:
            raise MONDOException(f"COULD NOT process MONDO input data from '{self.mondo_input}' due to '{e}'")
        else:
            self.set_phenotype()

    def save_mondo(self, output_filename):
        """
        Persist the current MONDO data model instance to the given destination path

        :param output_filename: destination file path
        :return: file path where the data model has been persisted
        """
        try:
            with jsonlines.open(output_filename, mode='w') as writer:
                for elem in self.mondo:
                    writer.write(self.mondo[elem])
        except Exception as e:
            raise MONDOException(f"COULD NOT save MONDO data to '{output_filename}' due to '{e}'")
        return output_filename
