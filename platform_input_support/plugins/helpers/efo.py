"""EFO Helper.

The current implementation is based on the conversion from owl format to
json lines format using Apache RIOT.

The structure disease_obsolete stores the obsolete terms and it is used to
retrieve the relationship between valid term and obsolete terms.

The locationIds are generated retrieving the structure parent/child and
recursively retrieve the proper info.
"""

import json
import logging
import re
from urllib import parse

import jsonlines

logger = logging.getLogger(__name__)


class EFOError(Exception):
    """EFO helper exception class."""


class EFO:
    """EFO data modeling."""

    def __init__(self, efo_input: str, conf: dict) -> None:
        """EFO data model instance constructor based on the given efo_input.

        :parm efo_input: path to EFO input file
        """
        self.efo_input = efo_input
        self.conf = conf
        self.diseases = {}
        self.diseases_obsolete = {}
        self.has_location_ids = {}
        self.all_path = {}
        self.parent_child_tuples = []

    def init_disease(self, id, code):
        """Initialize a disease entry given its ID and code.

        :param id: disease ID
        :param code: disease code
        """
        self.diseases[id] = {}
        self.diseases[id]['id'] = id
        self.diseases[id]['code'] = code

    # return the cross reference for the phenotype.
    # ETL uses it with hpo-phenotypes-_yyyy-mm-dd_.jsonl
    def set_phenotypes(self, id, disease):
        """Set the db xrefs for the given disease ID if present.

        :param id: disease ID
        :param disease: disease information object
        """
        if 'hasDbXref' in disease:
            self.diseases[id]['dbXRefs'] = disease['hasDbXref']

    def set_definition(self, id, disease):
        """Set a definition for the given disease ID.

        If it exists in the given disease object according to the term
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
                if len(definitions) > 1:
                    self.diseases[id]['definition_alternatives'] = definitions[1:]

    def get_values(self, value):
        """Perform value cleanup.

        Strip the new line character from either a given string or all the elements in a list of strings and returns
        that as a list of strings.

        :param value: data where to strip the new line character from
        :return: a list of strings where the new line character has been stripped off
        """
        if isinstance(value, str):
            return [value.strip('\n')]
        else:
            return [x.strip() for x in value if isinstance(x, str)]

    def set_efo_synonyms(self, id, disease):
        """Set EFO synonyms.

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
        """Extract phenotype information.

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
        """Set 'SKO' data from existing related phenotypes in the provided disease information object.

        :param id: EFO data model entry ID
        :param disease: disease information object to extract SKO information from
        """
        if 'related' in disease:
            self.diseases[id]['sko'] = self.get_phenotypes(disease['related'])

    # Return if the term is a TherapeuticArea
    def set_therapeutic_area(self, id, disease):
        """Set whether it's a therapeutic area or not.

        :param id: ID for the EFO entry
        :param disease: disease information object
        """
        if 'oboInOwl:inSubset' in disease:
            self.diseases[id]['isTherapeuticArea'] = True
        else:
            self.diseases[id]['isTherapeuticArea'] = False

    def set_label(self, id, disease):
        """Set label data.

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
        """Set the parents for a term.

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
        """Replace ':' by a '_' in the given element string.

        :return: the given element string with its first ':' replaced by '_'
        """
        return elem.replace(':', '_')

    def get_prefix(self, id: str) -> str:
        """Get the right ontology URL prefix.

        :param id: term ID to find out the URL prefix for
        :return: the URL prefix recognised for the given term ID
            default value is returned if unmatched
        """
        url_prefix_map: dict = self.conf.url_prefix_mapping
        url_prefix_default: str = self.conf.url_prefix_mapping_default
        id_regex = re.match(r'^(.+?)_', id)
        identifier = id_regex.group(1)
        return url_prefix_map.get(identifier, url_prefix_default)

    def extract_id_from_uri(self, uri):
        """Extract term IDs.

        :param uri: URI information to extract term IDs from
        :return: the list of term IDs that have been extracted from the given URI data
        """
        new_terms = []
        uris_to_process = []
        if isinstance(uri, str):
            uris_to_process = [uri]
        elif isinstance(uri, list):
            uris_to_process = self.get_values(uri)

        # TODO investigate the case of empty URIs, which would result on no IDs
        for uri_i in uris_to_process:
            full_path = parse.urlsplit(uri_i).path
            # TODO I think what we are after here is the last part of the path, that would be [-1] element in the
            #  partition list
            new_terms.append(full_path.rpartition('/')[2])
        return new_terms

    # Get the id and create a standard output. Eg. EFO:123 -> EFO_123, HP:9392 -> HP_9392
    def get_id(self, id):
        """Get the ID and standardise it.

        :param id: string to exctract the ID from
        :return: the standardised version of the extracted ID
        """
        ordo = re.sub(r'^.*?ORDO/', '', id)
        return re.sub(r'^.*?:', '', ordo)

    # Check if the efo term is valid. term obsolete goes to a dedicated structure
    def is_obsolete(self, disease, disease_id):
        """Process possible deprecated terms.

        :param disease: disease information object
        :param disease_id: disease ID
        :return: True if 'owl:deprecated' was present in the given disease information object, False otherwise
        """
        if 'owl:deprecated' in disease:
            if 'IAO_0100001' in disease:
                for term in self.extract_id_from_uri(disease['IAO_0100001']):
                    if term in self.diseases_obsolete:
                        self.diseases_obsolete[term].append(disease_id)
                    else:
                        self.diseases_obsolete[term] = [disease_id]
            return True
        return False

    # LocationIds: This procedure fills in the structure parent,child
    # TODO WARNING 'disease_id' is not being used, is that on purpose?
    def set_location_ids_structure(self, disease_id, disease):
        """Populate possible parentage entries.

        :param disease_id: WARNING! This is supposed to be the parent ID, but it's not used in this method's logic
        :param disease: disease information object
        """
        collection = None
        if 'unionOf' in disease:
            collection = disease['unionOf']['@list']
        elif 'intersectionOf' in disease:
            collection = disease['intersectionOf']['@list']

        if collection is not None:
            for elem in collection:
                if elem.startswith('_:'):
                    self.parent_child_tuples.append((disease['@id'], elem))

    def load_type_class(self, disease, disease_id):
        """Set information related to labeling, definition, therapeutic areas, synonyms, phenotypes, parents, etc.

        Unless the given disease information is about a location ID.

        :param disease: disease information object
        :param disease_id: disease ID
        """
        if not disease['@id'].startswith('_:'):
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

    def get_obsolete_info(self):
        """Compute 'obsolete data'."""
        for k in self.diseases_obsolete:
            if k in self.diseases:
                self.diseases[k]['obsoleteTerms'] = list(self.diseases_obsolete[k])

    # LocationIds: This is part of the structure to retrieve the info about locationIds
    def get_children(self, node):
        """Retrieve all children for a node.

        :param node: EFO node to get children from
        :return: the list of children for the given EFO node
        """
        return [x[1] for x in self.parent_child_tuples if x[0] == node]

    # LocationIds: This is part of the structure to retrieve the info about locationIds.
    # Recursively retrieve the location.
    def get_nodes(self, node, path):
        """Compute all the location ID children under a given node.

        :param node: node to get the children for
        :param path: already visited nodes
        :return: all the location ID children for the given node, taking into account the already visited nodes
        """
        data = set()
        data.add(node)
        path.add(node)
        children = self.get_children(node)
        if children:
            lista = set()
            for child in children:
                if not child.startswith('obo:'):
                    lista.update(self.get_nodes(child, path))
                else:
                    child_clean_code = re.sub(r'^.*?:', '', child)
                    lista.add(child_clean_code)
            data.update(lista)
        return data

    # LocationIds are stored in the restriction tag.
    # The info are stored inside a structure json parent-child
    def get_location_ids(self):
        """Compute location IDs."""
        # NOTE We could probably get a slight performance improvement here by making both lists into sets
        parents, children = zip(*self.parent_child_tuples)  # noqa: B905
        self.root_nodes = {x for x in parents if x not in children}
        for node in self.root_nodes:
            result = self.get_nodes(node, set())
            # self.all_path[node] = [x for x in list(result) if not x.startswith('_:')]
            # A set is iterable, nevertheless, I leave the original line here ^ for future reference
            self.all_path[node] = [x for x in result if not x.startswith('_:')]

        for k, v in self.has_location_ids.items():
            if k in self.all_path:
                if 'locationIds' not in self.diseases[v]:
                    self.diseases[v]['locationIds'] = set()
                self.diseases[v]['locationIds'].update(self.all_path[k])

    # For any term it generates the dict id info.
    def generate(self):
        """Compute the dictionary ID information."""
        try:
            with open(self.efo_input) as _input:
                for line in _input:
                    disease = json.loads(line)
                    disease_id = self.get_id(disease['@id'])
                    if not self.is_obsolete(disease, disease_id):
                        if disease['@type'] == 'owl:Class':
                            self.load_type_class(disease, disease_id)
                        # @Type: owl:Restriction
                        elif 'someValuesFrom' in disease:
                            self.parent_child_tuples.append((disease['@id'], disease['someValuesFrom']))
        except Exception as e:
            # TODO - Find out why AttributeError is not caught here and it keeps going up the chain
            # breaking the pipeline
            raise EFOError(f"Error computing EFO ID dictionary information due to '{e}'") from e
        else:
            self.get_obsolete_info()
            self.get_location_ids()

    # Static file for alpha and production
    def save_static_disease_file(self, output_filename):
        """Produce the static disease file given a destination path for the current EFO data model instance.

        :param output_filename: output file path
        """
        valid_keys = ['parents', 'id', 'label']
        try:
            with jsonlines.open(output_filename, mode='w') as writer:
                for _id in self.diseases:
                    entry = {k: v for k, v in self.diseases[_id].items() if k in valid_keys}
                    entry['parentIds'] = entry['parents']
                    del entry['parents']
                    entry['name'] = entry['label']
                    del entry['label']
                    writer.write(entry)
        except Exception as e:
            # TODO - Find out why AttributeError is not caught here and it keeps going up the chain
            # breaking the pipeline
            raise EFOError(f"COULD NOT save static disease file to '{output_filename}', due to '{e}'") from e

    def save_diseases(self, output_filename):
        """Persist disease data to a given destination file path.

        :param output_filename: output file path
        :return: the output file path where the data has been persisted
        """
        try:
            with jsonlines.open(output_filename, mode='w') as writer:
                for disease in self.diseases:
                    # Set cannot be transform in Json. Transform into list.
                    if 'locationIds' in self.diseases[disease]:
                        self.diseases[disease]['locationIds'] = list(self.diseases[disease]['locationIds'])
                    writer.write(self.diseases[disease])
        except Exception as e:
            # TODO - Find out why AttributeError is not caught here and it keeps going up the chain,
            # breaking the pipeline
            raise EFOError(f"COULD NOT diseases file to '{output_filename}', due to '{e}'") from e

        return output_filename
