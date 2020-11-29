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
        self.diseases = {}
        self.all_path= {}
        self.parent_child_tuples = []
        self.hpo = {}

    def init_disease(self, id, code):
        self.all_path[id] = []
        self.diseases[id] = {}
        self.diseases[id]['id'] = id
        self.diseases[id]['code'] = code
        self.diseases[id]['path_codes'] = []
        self.diseases[id]['children'] = []
        self.diseases[id]['phenotypes'] = []
        self.diseases[id]['ontology'] = {}
        self.diseases[id]['ontology']['sources'] = {'url': code, 'name': id}


    def get_hpo_mapping(self):
        return self.hpo

    def set_hpo_info(self, id, dbXrefs):
        for dbXref in dbXrefs:
            if dbXref in self.hpo:
                self.hpo[dbXref].append(id)
            else:
                self.hpo[dbXref] = [id]

    def set_phenotypes(self, id, disease):
        if 'hasDbXref' in disease:
            self.diseases[id]['phenotypes'] = disease['hasDbXref']
            self.set_hpo_info(id, disease['hasDbXref'])

    def set_definition(self, id, disease):
        if 'IAO_0000115' in disease:
            type(disease['IAO_0000115'])
            if isinstance(disease['IAO_0000115'], str):
                self.diseases[id]['definition'] = disease['IAO_0000115']
            else:
                self.diseases[id]['definition'] = disease['IAO_0000115'][0]
                self.diseases[id]['definition_alternatives'] = disease['IAO_0000115'][1:]

    def get_array_value(self, value):
        if isinstance(value, str):
            return [value]
        else:
            return value

    def set_efo_synonyms(self, id, disease):
        self.diseases[id]['efo_synonyms'] = {}
        if 'hasExactSynonym' in disease:
            self.diseases[id]['efo_synonyms']['hasExactSynonym'] = self.get_array_value(disease['hasExactSynonym'])

        if 'hasRelatedSynonym' in disease:
            self.diseases[id]['efo_synonyms']['hasRelatedSynonym'] = self.get_array_value(disease['hasRelatedSynonym'])

        if 'hasRelatedSynonym' in disease:
            self.diseases[id]['efo_synonyms']['hasRelatedSynonym'] = self.get_array_value(disease['hasRelatedSynonym'])

        if 'hasSynonym' in disease:
            self.diseases[id]['efo_synonyms']['hasSynonym'] = self.get_array_value(disease['hasSynonym'])

        if 'hasSynonym' in disease:
            self.diseases[id]['efo_synonyms']['hasNarrowSynonym'] = self.get_array_value(disease['hasNarrowSynonym'])

    # skos: related
    def get_phenotypes(self, phenotypes):
        if isinstance(phenotypes, str):
            return [self.get_id(phenotypes)]
        else:
            return [self.get_id(phenotype) for phenotype in phenotypes]

    def set_phenotypes_old(self, id, disease):
        if "related" in disease:
            self.diseases[id]['phenotypes_old'] = self.get_phenotypes(disease["related"])

    def set_therapeutic_area(self, id, disease):
        if 'oboInOwl:inSubset' in disease:
            self.diseases[id]['ontology']['isTherapeuticArea'] = True
        else:
            self.diseases[id]['ontology']['isTherapeuticArea'] = False

    def set_label(self,id, disease):
        if 'label' in disease:
            if isinstance(disease['label'], str):
                self.diseases[id]['label'] = disease['label']
            elif isinstance(disease['label'], dict):
                self.diseases[id]['label'] = disease['label']['@value']
            else:
                self.diseases[id]['label'] = disease['label'][0]

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

    def get_prefix(self,id):
        simple_id = re.match(r'^(.+?)_', id)
        if simple_id.group() in ["EFO_", "OTAR_"]:
            return "http://www.ebi.ac.uk/efo/"
        elif (simple_id.group() in 'Orphanet_'):
            return "http://www.orpha.net/ORDO/"
        else:
            return "http://purl.obolibrary.org/obo/"

    def get_id(self, id):
        ordo = re.sub(r'^.*?ORDO/', '', id)
        new_id = re.sub(r'^.*?:', '', ordo)
        return new_id

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

    def get_children(self, node):
        return [x[1] for x in self.parent_child_tuples if x[0] == node]

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
                #self.set_phenotypes_old(disease_id, disease)
                self.set_parents(disease_id, disease)


        parents, children = zip(*self.parent_child_tuples)
        self.root_nodes = {x for x in parents if x not in children}

    def create_paths(self):
        tree = []
        for node in self.root_nodes:
            print("Therapeutic Area: " + node)
            c = self.get_nodes(node, [])
            tree.append(c)

        #n_tree = [self.get_nodes(node, []) for node in self.root_nodes]

    def save_diseases(self):
        with jsonlines.open(PIS_OUTPUT_ANNOTATIONS+'/efo-new.jsonl', mode='w') as writer:
            for disease in self.diseases:
                if len(self.diseases[disease]['children']) > 0:
                    self.diseases[disease]['ontology']['leaf'] = False
                else:
                    self.diseases[disease]['ontology']['leaf'] = True

                if disease in self.all_path:
                    self.diseases[disease]['path_codes'] = self.all_path[disease]
                    self.diseases[disease]['therapeutic_codes'] = list(set(item for sublist in self.all_path[disease] for item in sublist).intersection(self.root_nodes))

                writer.write(self.diseases[disease])
