import json
import re

import jsonlines
from loguru import logger


class HPOError(Exception):
    """HPO helper exception class."""


class HPO:
    def __init__(self, hpo_input):
        """HPO Helper constructor.

        :param hpo_input: input data file path
        """
        self.hpo_input = hpo_input
        self.hpo = {}
        self.hpo_obsolete = {}

    def init_hp(self, id):
        """Initialize an entry.

        :param id: term ID
        """
        self.hpo[id] = {}
        self.hpo[id]['id'] = id

    def extract_id(self, elem):
        """Normalize the ID by replacing ':' for '_'.

        :param elem: term to normalise
        :return: the normalised ID
        """
        return elem.replace(':', '_')

    def get_id(self, hp):
        """Extract term ID or skip it in case it contains no ID.

        :param hp: term to extract ID from
        :return: the extracted ID, None otherwise
        """
        if 'id' in hp:
            return hp['id'].replace(':', '_')
        elif '@id' in hp:
            return re.sub(r'^.*?:', '', hp['@id']).replace(':', '_')
        else:
            logger.debug(f'skip this id: {hp}')

    def is_not_obsolete(self, id, hpo):
        """Check that a given HPO term is not obsolete.

        :param hpo: term to check
        :return: True if NOT obsolete, False otherwise
        """
        return not self.is_obsolete(hpo)

    def is_obsolete(self, hpo):
        """Check whether an HPO term is obsolete or not.

        :param hpo: term to check
        :return: True if obsolete, False otherwise
        """
        return 'owl:deprecated' in hpo

    def set_label(self, id, hpo):
        """Set the HPO label information.

        :param id: term ID
        :param hpo: HPO information object
        """
        if 'label' in hpo:
            if isinstance(hpo['label'], str):
                self.hpo[id]['name'] = hpo['label']
            elif isinstance(hpo['label'], dict):
                self.hpo[id]['name'] = hpo['label']['@value']
            elif isinstance(hpo['label'][0], str):
                self.hpo[id]['name'] = hpo['label'][0]
            else:
                self.hpo[id]['name'] = hpo['label'][0]['@value']

    def get_father(self, id):
        """Get the father term.

        :param id: term ID
        :return: father ID
        """
        # NOTE I guess the plarentage information is encoded in the ID itself...
        return re.sub(r'^.*?:', '', id)

    def set_parents(self, id, hpo):
        """Set parentage information.

        :param id: HPO ID
        :param hpo: HPO information object
        """
        parents = []
        if 'subClassOf' in hpo:
            if isinstance(hpo['subClassOf'], str):
                parents.append(self.get_father(hpo['subClassOf']))
            else:
                for father in hpo['subClassOf']:
                    parents.append(self.get_father(father))  # noqa: PERF401
            self.hpo[id]['parents'] = parents

    def set_phenotypes(self, id, hpo):
        """Set phenotype data, i.e. phenotypes.

        :param id: term ID
        :param hpo: HPO information object
        """
        db_xrefs = []
        if 'hasDbXref' in hpo:
            if isinstance(hpo['hasDbXref'], str):
                db_xrefs.append(hpo['hasDbXref'])
            else:
                for ref in hpo['hasDbXref']:
                    db_xrefs.append(ref)  # noqa: PERF402

            self.hpo[id]['dbXRefs'] = db_xrefs

    def set_description(self, id, hpo):
        """Set description information.

        :param id: term ID
        :param hpo: HPO information object
        """
        if 'IAO_0000115' in hpo:
            if isinstance(hpo['IAO_0000115'], str):
                self.hpo[id]['description'] = hpo['IAO_0000115']
            elif '@value' in hpo['IAO_0000115']:
                self.hpo[id]['description'] = hpo['IAO_0000115']['@value']
            else:
                self.hpo[id]['description'] = hpo['IAO_0000115'][0]

    def set_namespace(self, id, hpo):
        """Set the namespace information.

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
                        namespace.append(ns)  # noqa: PERF401
        elif re.match(r'^.*?HP', id):
            self.hpo[id]['namespace'] = namespace.append('human_phenotype')

        self.hpo[id]['namespace'] = namespace

    def set_obsoleted_term(self, id, hpo):
        """Compute obsolete term data.

        :param id: term ID
        :param hpo: HPO information object
        """
        if 'hasAlternativeId' in hpo:
            obsolete = []
            if isinstance(hpo['hasAlternativeId'], str):
                obsolete.append(self.extract_id(hpo['hasAlternativeId']))
            else:
                for term in hpo['hasAlternativeId']:
                    obsolete.append(self.extract_id(term))  # noqa: PERF401

            self.hpo[id]['obsolete_terms'] = obsolete

    def generate(self):
        """Compute the HPO data model instance."""
        try:
            with open(self.hpo_input) as _input:
                for line in _input:
                    hp = json.loads(line)
                    hpo_id = self.get_id(hp)
                    if self.is_not_obsolete(hpo_id, hp):
                        self.init_hp(hpo_id)
                        self.set_obsoleted_term(hpo_id, hp)
                        self.set_namespace(hpo_id, hp)
                        self.set_description(hpo_id, hp)
                        self.set_label(hpo_id, hp)
                        self.set_parents(hpo_id, hp)
                        self.set_phenotypes(hpo_id, hp)
        except Exception as e:
            raise HPOError(f"COULD NOT read HPO input dataset from '{self.hpo_input}' due to '{e}'")

    def save_hpo(self, output_filename):
        """Persist the current HPO data model.

        :param output_filename: destination file path for persisting the current HPO data model
        """
        try:
            with jsonlines.open(output_filename, mode='w') as writer:
                for hp in self.hpo:
                    writer.write(self.hpo[hp])
        except Exception as e:
            raise HPOError(f"COULD NOT save HPO data to '{output_filename}' due to '{e}'")
        return output_filename
