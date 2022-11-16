import re
import json
import logging
import jsonlines

logger = logging.getLogger(__name__)


class HPOException(Exception):
    pass


class HPO(object):

    def __init__(self, hpo_input):
        """
        Constructor

        :param hpo_input: input data file path
        """
        self.hpo_input = hpo_input
        self.hpo = {}
        self.hpo_obsolete = {}

    def init_hp(self, id):
        """
        Initialize the entry for the given term ID in the current HPO data model instance

        :param id: term ID
        """
        self.hpo[id] = {}
        self.hpo[id]['id'] = id

    def extract_id(self, elem):
        """
        Given a term, this method 'normalises' the ID by replacing ':' for '_'

        :param elem: term to normalise
        :return: the normalised ID
        """
        return elem.replace(":", "_")

    def get_id(self, hp):
        """
        Extract term ID from the given HPO term or skip it in case it contains no ID

        :param hp: term to extract ID from
        :return: the extracted ID, None otherwise
        """
        if 'id' in hp:
            return hp['id'].replace(":", "_")
        elif '@id' in hp:
            return re.sub(r'^.*?:', '', hp['@id']).replace(":", "_")
        else:
            logger.debug("skip this id:" + hp)

    def is_not_obsolete(self, id, hpo):
        """
        Check that a given HPO term is not obsolete

        :param hpo: term to check
        :return: True if NOT obsolete, False otherwise
        """
        return not self.is_obsolete(hpo)

    def is_obsolete(self, hpo):
        """
        Check whether an HPO term is obsolete or not

        :param hpo: term to check
        :return: True if obsolete, False otherwise
        """
        return 'owl:deprecated' in hpo

    def set_label(self, id, hpo):
        """
        Set the HPO label information for the given term ID in the current HPO data model instance

        :param id: term ID
        :param hpo: HPO information object
        """
        if 'label' in hpo:
            if isinstance(hpo['label'], str):
                self.hpo[id]['name'] = hpo['label']
            elif isinstance(hpo['label'], dict):
                self.hpo[id]['name'] = hpo['label']['@value']
            else:
                if isinstance(hpo['label'][0], str):
                    self.hpo[id]['name'] = hpo['label'][0]
                else:
                    self.hpo[id]['name'] = hpo['label'][0]['@value']

    def get_father(self, id):
        """
        Get the father term for the given term ID

        :param id: term ID
        :return: father ID
        """
        # NOTE I guess the plarentage information is encoded in the ID itself...
        return re.sub(r'^.*?:', '', id)

    def set_parents(self, id, hpo):
        """
        Set parentage information for a given HPO ID given an HPO information object

        :param id: HPO ID
        :param hpo: HPO information object
        """
        parents = []
        if 'subClassOf' in hpo:
            if isinstance(hpo['subClassOf'], str):
                parents.append(self.get_father(hpo['subClassOf']))
            else:
                for father in hpo['subClassOf']:
                    parents.append(self.get_father(father))
            self.hpo[id]['parents'] = parents

    def set_phenotypes(self, id, hpo):
        """
        Set phenotype data, i.e. phenotypes, for the given term ID as per the information in the given HPO object

        :param id: term ID
        :param hpo: HPO information object
        """
        dbXRefs = []
        if 'hasDbXref' in hpo:
            if isinstance(hpo['hasDbXref'], str):
                dbXRefs.append(hpo['hasDbXref'])
            else:
                for ref in hpo['hasDbXref']:
                    dbXRefs.append(ref)

            self.hpo[id]['dbXRefs'] = dbXRefs

    def set_description(self, id, hpo):
        """
        Set the description information for a term ID in the current HPO data model instance, according to the given HPO
        data object

        :param id: term ID
        :param hpo: HPO information object
        """
        if 'IAO_0000115' in hpo:
            if isinstance(hpo['IAO_0000115'], str):
                self.hpo[id]['description'] = hpo['IAO_0000115']
            else:
                if '@value' in hpo['IAO_0000115']:
                    self.hpo[id]['description'] = hpo['IAO_0000115']['@value']
                else:
                    self.hpo[id]['description'] = hpo['IAO_0000115'][0]

    def set_namespace(self, id, hpo):
        """
        Set the namespace information for a term ID in the current HPO data model instance, according to the given HPO
        data object

        :param id: term ID
        :param hpo: HPO information object
        """
        namespace = []
        if 'hasOBONamespace' in hpo:
            if isinstance(hpo['hasOBONamespace'], str):
                namespace.append(hpo['hasOBONamespace'])
            else:
                for ns in hpo['hasOBONamespace']:
                    if ns != 'none':
                        namespace.append(ns)
        else:
            if re.match(r'^.*?HP', id):
                self.hpo[id]['namespace'] = namespace.append("human_phenotype")

        self.hpo[id]['namespace'] = namespace

    def set_obsoleted_term(self, id, hpo):
        """
        Compute obsolete term data for the given term ID according to an HPO information object, in the current HPO data
        model instance

        :param id: term ID
        :param hpo: HPO information object
        """
        if "hasAlternativeId" in hpo:
            obsolete = []
            if isinstance(hpo['hasAlternativeId'], str):
                obsolete.append(self.extract_id(hpo['hasAlternativeId']))
            else:
                for term in hpo['hasAlternativeId']:
                    obsolete.append(self.extract_id(term))

            self.hpo[id]['obsolete_terms'] = obsolete

    def generate(self):
        """
        Compute the HPO data model instance for the given input data file
        """
        try:
            with open(self.hpo_input) as input:
                for line in input:
                    hp = json.loads(line)
                    id = self.get_id(hp)
                    if self.is_not_obsolete(id, hp):
                        self.init_hp(id)
                        self.set_obsoleted_term(id, hp)
                        self.set_namespace(id, hp)
                        self.set_description(id, hp)
                        self.set_label(id, hp)
                        self.set_parents(id, hp)
                        self.set_phenotypes(id, hp)
        except Exception as e:
            raise HPOException(f"COULD NOT read HPO input dataset from '{self.hpo_input}' due to '{e}'")

    def save_hpo(self, output_filename):
        """
        Persist the current HPO data model instance to the given destination file path

        :param output_filename: destination file path for persisting the current HPO data model
        """
        try:
            with jsonlines.open(output_filename, mode='w') as writer:
                for hp in self.hpo:
                    writer.write(self.hpo[hp])
        except Exception as e:
            raise HPOException(f"COULD NOT save HPO data to '{output_filename}' due to '{e}'")
        return output_filename
