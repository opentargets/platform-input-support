import logging
import re
import json
import jsonlines
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS

logger = logging.getLogger(__name__)


class EFO(object):

    def __init__(self, efo_input):
        self.efo_input = efo_input
        self.root_nodes = None
        self.therapeutic_area =[]
        self.diseases = {}
        self.all_path= {}
        self.parent_child_tuples = []

    def init_disease(self, id, code):
        self.all_path[id] = []
        self.diseases[id] = {}
        self.diseases[id]['id'] = id
        self.diseases[id]['code'] = code
        self.diseases[id]['path_codes'] = []
        self.diseases[id]['children'] = []
        self.diseases[id]['ontology'] = {}
        self.diseases[id]['ontology']['sources'] = {'url': code, 'name': id}

    # return the cross reference for the phenotype.
    # ETL uses it with hpo-phenotypes-_yyyy-mm-dd_.jsonl
    def set_phenotypes(self, id, disease):
        if 'hasDbXref' in disease:
            self.diseases[id]['dbXRefs'] = disease['hasDbXref']

    def set_definition(self, id, disease):
        if 'IAO_0000115' in disease:
            type(disease['IAO_0000115'])
            if isinstance(disease['IAO_0000115'], str):
                self.diseases[id]['definition'] = disease['IAO_0000115'].strip('\n')
            else:
                self.diseases[id]['definition'] = disease['IAO_0000115'][0].strip('\n')
                self.diseases[id]['definition_alternatives'] = disease['IAO_0000115'][1:]

    # Return an array of strings without new line.
    def get_array_value(self, value):
        if isinstance(value, str):
            return [value.strip('\n')]
        else:
            return [x.strip() for x in value]

    # Return the synonyms
    def set_efo_synonyms(self, id, disease):
        synonyms_details = {}
        if 'hasExactSynonym' in disease:
            if len(disease['hasExactSynonym']) >0:
                synonyms = self.get_array_value(disease['hasExactSynonym'])
                synonyms_details['hasExactSynonym'] = synonyms

        if 'hasRelatedSynonym' in disease:
            if len(disease['hasRelatedSynonym']) >0:
                synonyms = self.get_array_value(disease['hasRelatedSynonym'])
                synonyms_details['hasRelatedSynonym'] = synonyms

        if 'hasBroadSynonym' in disease:
            if len(disease['hasBroadSynonym']) >0:
                synonyms =  self.get_array_value(disease['hasBroadSynonym'])
                synonyms_details['hasBroadSynonym'] = synonyms

        if 'hasNarrowSynonym' in disease:
            if len(disease['hasNarrowSynonym']) >0:
                synonyms = self.get_array_value(disease['hasNarrowSynonym'])
                synonyms_details['hasNarrowSynonym'] = synonyms

        if len(synonyms_details.keys()) > 0:
            self.diseases[id]['synonyms'] = synonyms_details


    # Extract skos: related
    def get_phenotypes(self, phenotypes):
        if isinstance(phenotypes, str):
            return [self.get_id(phenotypes)]
        else:
            return [self.get_id(phenotype) for phenotype in phenotypes]

    # The field sko is used to check if the phenotype cross references are correct.
    # ETL - GraphQL test.
    def set_phenotypes_old(self, id, disease):
        if "related" in disease:
            self.diseases[id]['sko'] = self.get_phenotypes(disease["related"])

    # Return if the term is a TherapeuticArea
    def set_therapeutic_area(self, id, disease):
        if 'oboInOwl:inSubset' in disease:
            self.diseases[id]['ontology']['isTherapeuticArea'] = True
            self.therapeutic_area.append(id)
        else:
            self.diseases[id]['ontology']['isTherapeuticArea'] = False

    # Return the label of the term
    def set_label(self,id, disease):
        if 'label' in disease:
            if isinstance(disease['label'], str):
                self.diseases[id]['label'] = disease['label'].strip('\n')
            elif isinstance(disease['label'], dict):
                self.diseases[id]['label'] = disease['label']['@value'].strip('\n')
            else:
                self.diseases[id]['label'] = disease['label'][0].strip('\n')


    # Return the parents for the term
    def set_parents(self,id,disease):
        if 'subClassOf' in disease:
            subset = disease['subClassOf']
            parents = []
            if len(subset) > 0:
                for father in subset:
                    father_id = self.get_id(father)
                    parents.append(father_id)
                    self.parent_child_tuples.append((father_id,id))

            self.diseases[id]['parents'] = parents


    def extract_id(self, elem):
        return elem.replace(":", "_")

    # list of obsolete term
    def set_obsoleted_term(self, id, disease):
        if "hasAlternativeId" in disease:
            obsolete = []
            if isinstance(disease['hasAlternativeId'], str):
                obsolete.append(self.extract_id(disease['hasAlternativeId']))
            else:
                for term in disease['hasAlternativeId']:
                    obsolete.append(self.extract_id(term))
            if len(obsolete) > 0:
                self.diseases[id]['obsolete_terms'] = obsolete

    # return the proper prefix.
    def get_prefix(self,id):
        simple_id = re.match(r'^(.+?)_', id)
        if simple_id.group() in ["EFO_", "OTAR_"]:
            return "http://www.ebi.ac.uk/efo/"
        elif (simple_id.group() in 'Orphanet_'):
            return "http://www.orpha.net/ORDO/"
        else:
            return "http://purl.obolibrary.org/obo/"

    # Get the id and create a standard output. Eg. EFO:123 -> EFO_123, HP:9392 -> HP_9392
    def get_id(self, id):
        ordo = re.sub(r'^.*?ORDO/', '', id)
        new_id = re.sub(r'^.*?:', '', ordo)
        return new_id

    # Build the children list for the node.
    def get_nodes(self, node, path):
        data = {}
        data['name'] = node
        path.append(node)
        children = self.get_children(node)
        if children:
            self.diseases[node]['children'] = list(set(children) | set(self.diseases[node]['children']))
            lista = []
            for child in children:
                lista.append(self.get_nodes(child, path))
            data["children"] = lista
        if node in self.all_path:
            self.all_path[node].append(path.copy())
        else:
            self.all_path[node] = [path.copy()]
        path.remove(node)
        return data

    # parent_child_tuples contains (father, child) relationship.
    # This function retrienve all the children for the node requested.
    def get_children(self, node):
        return [x[1] for x in self.parent_child_tuples if x[0] == node]

    # For any term it generates the dict id info.
    def generate(self):
        with open(self.efo_input) as input:
            for line in input:
                disease = json.loads(line)
                disease_id = self.get_id(disease['@id'])
                code = self.get_prefix(disease_id) + disease_id
                self.init_disease(disease_id, code)
                self.set_label(disease_id, disease)
                self.set_definition(disease_id, disease)
                self.set_therapeutic_area(disease_id,disease)
                self.set_efo_synonyms(disease_id,disease)
                self.set_phenotypes(disease_id, disease)
                self.set_obsoleted_term(disease_id, disease)
                self.set_phenotypes_old(disease_id, disease)
                self.set_parents(disease_id, disease)


        parents, children = zip(*self.parent_child_tuples)
        self.root_nodes = {x for x in parents if x not in children}

    def create_paths(self):
        logging.info("==> Create paths for disease")
        #tree = []
        #for node in self.root_nodes:
        #    print("Therapeutic Area: " + node)
        #    c = self.get_nodes(node, [])
        #    tree.append(c)
        tree = [self.get_nodes(node, []) for node in self.root_nodes]

    # Static file for alpha and production
    def save_static_disease_file(self, output_filename):
        valid_keys = ["parents", "id", "label"]
        with jsonlines.open(PIS_OUTPUT_ANNOTATIONS+'/'+output_filename, mode='w') as writer:
            for id in self.diseases:
                entry = {k: v for k, v in self.diseases[id].items() if k in valid_keys}
                entry["parentIds"] = entry["parents"]
                # TODO: next release remove this code. BUG for the efo_otar_slim.owl
                del(entry["parents"])
                if "label" in entry:
                    entry["name"] = entry["label"]
                    del(entry["label"])
                else:
                    print("Issue with the TERM: " + entry["id"])

                writer.write(entry)

    def save_diseases(self, output_filename):
        with jsonlines.open(PIS_OUTPUT_ANNOTATIONS+'/'+output_filename, mode='w') as writer:
            for disease in self.diseases:
                if len(self.diseases[disease]['children']) > 0:
                    self.diseases[disease]['ontology']['leaf'] = False
                else:
                    self.diseases[disease]['ontology']['leaf'] = True

                if disease in self.all_path:
                    self.diseases[disease]['path_codes'] = self.all_path[disease]
                    self.diseases[disease]['therapeutic_codes'] = list(set(item for sublist in self.all_path[disease] for item in sublist).intersection(self.root_nodes))

                writer.write(self.diseases[disease])
