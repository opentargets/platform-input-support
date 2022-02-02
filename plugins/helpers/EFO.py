import re
import json
import logging
import jsonlines
from urllib import parse

logger = logging.getLogger(__name__)

"""
- EFO -
The current implementation is based on the conversion from owl format to json lines format using Apache RIOT
The structure disease_obsolete stores the obsolete terms and it is used to retrieve the relationship between valid
    term and obsolete terms.
The locationIds are generated retriving the structure parent/child and recursevely retrieve the proper info
"""


class EFO(object):
    """
    EFO Data modeling
    """

    def __init__(self, efo_input):
        """
        Constructor for EFO data model instance based on the given efo_input

        :parm efo_input: path to EFO input file
        """
        self.efo_input = efo_input
        self.diseases = {}
        self.diseases_obsolete = {}
        self.has_location_ids = {}
        self.all_path = {}
        self.parent_child_tuples = []

    def init_disease(self, id, code):
        """
        Initialize a disease entry given its ID and code

        :param id: disease ID
        :param code: disease code
        """
        self.diseases[id] = {}
        self.diseases[id]['id'] = id
        self.diseases[id]['code'] = code

    # return the cross reference for the phenotype.
    # ETL uses it with hpo-phenotypes-_yyyy-mm-dd_.jsonl
    def set_phenotypes(self, id, disease):
        """
        Set the db xrefs for the given disease ID if present, in the current EFO model

        :param id: disease ID
        :param disease: disease information object
        """
        if 'hasDbXref' in disease:
            self.diseases[id]['dbXRefs'] = disease['hasDbXref']

    def set_definition(self, id, disease):
        """
        Set a definition for the given disease ID if it exists in the given disease object according to the term
        http://www.ontobee.org/ontology/IAO?iri=http://purl.obolibrary.org/obo/IAO_0000115

        If multiple definitions are present in the given 'disease' object, the first one will be set as the main
        definition, and the rest as alternative ones.

        :param id: disease ID
        :param disease: disease information object
        """
        if 'IAO_0000115' in disease:
            if isinstance(disease['IAO_0000115'], str):
                # The case where the disease definition is just one string
                self.diseases[id]['definition'] = disease['IAO_0000115'].strip('\n')
            else:
                # In the case the disease definition is multiple (strings), it will pick the first one as the main
                # definition, and set the others as alternative definitions
                definitions = self.get_values(disease['IAO_0000115'])
                self.diseases[id]['definition'] = definitions[0]
                if len(definitions) > 1: self.diseases[id]['definition_alternatives'] = definitions[1:]

    def get_values(self, value):
        """
        Strip the new line character from either a given string or all the elements in a list of strings and return that
        as a list of strings

        :param value: data where to strip the new line character from
        :return: a list of strings where the new line character has been stripped off
        """
        if isinstance(value, str):
            return [value.strip('\n')]
        else:
            return [x.strip() for x in value if isinstance(x, str)]

    def set_efo_synonyms(self, id, disease):
        """
        Set EFO synonyms for the given ID in the current EFO model using the given disease data.

        :param id: EFO model entry ID
        :param disease: disease information object
        """
        synonyms_details = {}
        if 'hasExactSynonym' in disease and len(disease['hasExactSynonym']) > 0:
            synonyms_details['hasExactSynonym'] = self.get_values(disease['hasExactSynonym'])

        if 'hasRelatedSynonym' in disease and len(disease['hasRelatedSynonym']) > 0:
            synonyms_details['hasRelatedSynonym'] = self.get_values(disease['hasRelatedSynonym'])

        if 'hasBroadSynonym' in disease and len(disease['hasBroadSynonym']) > 0:
            synonyms_details['hasBroadSynonym'] = self.get_values(disease['hasBroadSynonym'])

        if 'hasNarrowSynonym' in disease and len(disease['hasNarrowSynonym']) > 0:
            synonyms_details['hasNarrowSynonym'] = self.get_values(disease['hasNarrowSynonym'])

        if len(synonyms_details.keys()) > 0:
            self.diseases[id]['synonyms'] = synonyms_details

    def get_phenotypes(self, phenotypes):
        """
        Extract phenotype information as a list of phenotypes from the given phenotype information object.

        :param phenotypes: Phenotypes information object
        :return: a list of the extracted phenotypes
        """
        if isinstance(phenotypes, str):
            return [self.get_id(phenotypes)]
        else:
            return [self.get_id(phenotype) for phenotype in phenotypes]

    # The field sko is used to check if the phenotype cross references are correct.
    # ETL - GraphQL test.
    def set_phenotypes_old(self, id, disease):
        """
        Set 'SKO' data from existing related phenotypes in the provided disease information object for the given EFO
        data model entry ID

        :param id: EFO data model entry ID
        :param disease: disease information object to extract SKO information from
        """
        if "related" in disease:
            self.diseases[id]['sko'] = self.get_phenotypes(disease["related"])

    # Return if the term is a TherapeuticArea
    def set_therapeutic_area(self, id, disease):
        """
        For the given EFO data model entry ID, and a disease information object, set whether it's a therapeutic area or
        not

        :param id: ID for the EFO entry
        :param disease: disease information object
        """
        if 'oboInOwl:inSubset' in disease:
            self.diseases[id]['isTherapeuticArea'] = True
        else:
            self.diseases[id]['isTherapeuticArea'] = False

    def set_label(self, id, disease):
        """
        Set the label data for the given EFO entry ID with information in the given disease information object.

        :param id: EFO entry ID in the current data model
        :param disease: disease information object
        """
        if 'label' in disease:
            if isinstance(disease['label'], str):
                self.diseases[id]['label'] = disease['label'].strip('\n')
            elif isinstance(disease['label'], dict):
                self.diseases[id]['label'] = disease['label']['@value'].strip('\n')
            else:
                self.diseases[id]['label'] = self.get_values(disease['label'])[0]

    def set_parents(self, id, disease):
        """
        Set the parents for the given term ID in the current EFO data model instance, according to the information in
        the given disease object

        :param id: term ID
        :param disease: disease information object
        """
        if 'subClassOf' in disease:
            parents = []
            for father in disease['subClassOf']:
                if father.startswith('_:'):
                    self.has_location_ids[father] = id
                else:
                    father_id = self.get_id(father)
                    parents.append(father_id)
            self.diseases[id]['parents'] = parents

    def extract_id(self, elem):
        return elem.replace(":", "_")

    # return the proper prefix.
    def get_prefix(self, id):
        simple_id = re.match(r'^(.+?)_', id)
        if simple_id.group() in ["EFO_", "OTAR_"]:
            return "http://www.ebi.ac.uk/efo/"
        elif (simple_id.group() in 'Orphanet_'):
            return "http://www.orpha.net/ORDO/"
        else:
            return "http://purl.obolibrary.org/obo/"

    def extract_id_from_uri(self, uri):
        new_terms = []
        if isinstance(uri, str):
            uris_to_extract = [uri]
        elif isinstance(uri, list):
            uris_to_extract = self.get_values(uri)
        else:
            # todo: investigate to this case.
            uris_to_extract = []

        for uri_i in uris_to_extract:
            full_path = parse.urlsplit(uri_i).path
            new_terms.append(full_path.rpartition('/')[2])

        return new_terms

    # Get the id and create a standard output. Eg. EFO:123 -> EFO_123, HP:9392 -> HP_9392
    def get_id(self, id):
        ordo = re.sub(r'^.*?ORDO/', '', id)
        new_id = re.sub(r'^.*?:', '', ordo)
        return new_id

    # Check if the efo term is valid. term obsolete goes to a dedicated structure
    def is_obsolete(self, disease, disease_id):
        if 'owl:deprecated' in disease:
            if 'IAO_0100001' in disease:
                new_terms = self.extract_id_from_uri(disease['IAO_0100001'])
                for term in new_terms:
                    if term in self.diseases_obsolete:
                        self.diseases_obsolete[term].append(disease_id)
                    else:
                        self.diseases_obsolete[term] = [disease_id]
            return True
        else:
            return False

    # LocationIds: This procedure fills in the structure parent,child
    def set_locationIds_structure(self, disease_id, disease):
        collection = None
        if "unionOf" in disease:
            collection = disease["unionOf"]["@list"]
        elif "intersectionOf" in disease:
            collection = disease["intersectionOf"]["@list"]

        if collection is not None:
            for elem in collection:
                if elem.startswith('_:'):
                    self.parent_child_tuples.append((disease["@id"], elem))

    def load_type_class(self, disease, disease_id):
        if not disease["@id"].startswith('_:'):
            code = self.get_prefix(disease_id) + disease_id
            self.init_disease(disease_id, code)
            self.set_label(disease_id, disease)
            self.set_definition(disease_id, disease)
            self.set_therapeutic_area(disease_id, disease)
            self.set_efo_synonyms(disease_id, disease)
            self.set_phenotypes(disease_id, disease)
            self.set_phenotypes_old(disease_id, disease)
            self.set_parents(disease_id, disease)
        else:
            self.set_locationIds_structure(disease_id, disease)

    #
    def get_obsolete_info(self):
        for k, v in self.diseases_obsolete.items():
            if k in self.diseases:
                self.diseases[k]['obsoleteTerms'] = list(self.diseases_obsolete[k])

    # LocationIds: This is part of the structure to retrieve the info about locationIds
    def get_children(self, node):
        return [x[1] for x in self.parent_child_tuples if x[0] == node]

    # LocationIds: This is part of the structure to retrieve the info about locationIds.
    # Recursively retrieve the location.
    def get_nodes(self, node, path):
        data = set()
        data.add(node)
        path.add(node)
        children = self.get_children(node)
        if children:
            lista = set()
            for child in children:
                if not child.startswith("obo:"):
                    lista.update(self.get_nodes(child, path))
                else:
                    child_clean_code = re.sub(r'^.*?:', '', child)
                    lista.add(child_clean_code)
            data.update(lista)
        return data

    # LocationIds are stored in the restriction tag.
    # The info are stored inside a structure json parent-child
    def get_locationIds(self):
        parents, children = zip(*self.parent_child_tuples)
        self.root_nodes = {x for x in parents if x not in children}
        for node in self.root_nodes:
            result = self.get_nodes(node, set())
            self.all_path[node] = [x for x in list(result) if not x.startswith('_:')]

        for k, v in self.has_location_ids.items():
            if k in self.all_path:
                if not "locationIds" in self.diseases[v]:
                    self.diseases[v]["locationIds"] = set()
                self.diseases[v]["locationIds"].update(self.all_path[k])

    # For any term it generates the dict id info.
    def generate(self):
        with open(self.efo_input) as input:
            for line in input:
                disease = json.loads(line)
                disease_id = self.get_id(disease['@id'])
                if not self.is_obsolete(disease, disease_id):
                    if disease["@type"] == "Class":
                        self.load_type_class(disease, disease_id)
                    else:
                        # @Type: Restriction
                        if 'someValuesFrom' in disease:
                            self.parent_child_tuples.append((disease["@id"], disease["someValuesFrom"]))

        self.get_obsolete_info()
        self.get_locationIds()

    # Static file for alpha and production
    def save_static_disease_file(self, output_filename):
        valid_keys = ["parents", "id", "label"]
        with jsonlines.open(output_filename, mode='w') as writer:
            for id in self.diseases:
                entry = {k: v for k, v in self.diseases[id].items() if k in valid_keys}
                entry["parentIds"] = entry["parents"]
                del (entry["parents"])
                entry["name"] = entry["label"]
                del (entry["label"])

                writer.write(entry)

    def save_diseases(self, output_filename):
        with jsonlines.open(output_filename, mode='w') as writer:
            for disease in self.diseases:
                # Set cannot be transform in Json. Transform into list.
                if 'locationIds' in self.diseases[disease]:
                    listValues = list(self.diseases[disease]['locationIds'])
                    self.diseases[disease]['locationIds'] = listValues

                writer.write(self.diseases[disease])

        return output_filename
