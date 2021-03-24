import logging
import re
import json
import jsonlines
from urllib import parse
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS

logger = logging.getLogger(__name__)

# EFO
# The current implementation is based on the conversion from owl format to json lines format using Apache RIOT
# The structure restriction and class_restriction are used to retrieve location info.
# The structure disease_obsolete stores the obsolete terms and it is used to retrieve the relationship between valid
# term and obsolete terms.

class EFO(object):

    def __init__(self, efo_input):
        self.efo_input = efo_input
        self.root_nodes = None
        self.therapeutic_area =[]
        self.diseases = {}
        self.diseases_obsolete = {}
        self.restriction = {}
        self.class_restriction = {}
        self.has_location_ids = {}
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

    # Retrieve the definition info
    def set_definition(self, id, disease):
        if 'IAO_0000115' in disease:
            if isinstance(disease['IAO_0000115'], str):
                self.diseases[id]['definition'] = disease['IAO_0000115'].strip('\n')
            else:
                definitions=self.get_array_value(disease['IAO_0000115'])
                self.diseases[id]['definition'] = definitions[0]
                if len(definitions) > 1: self.diseases[id]['definition_alternatives'] = definitions[1:]

    # Return an array of strings without new line.
    def get_array_value(self, value):
        if isinstance(value, str):
            return [value.strip('\n')]
        else:
            return [x.strip() for x in value if isinstance(x,str)]

    # Return the synonyms. Complex structure. Clean and flatten.
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


    # Extract skos: related: used for check phenotype info.
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
                self.diseases[id]['label'] = self.get_array_value(disease['label'])[0]


    # Return the parents for the term
    def set_parents(self,id,disease):
        if 'subClassOf' in disease:
            subset = disease['subClassOf']
            parents = []
            if len(subset) > 0:
                for father in subset:
                    if father.startswith('_:'):
                        self.has_location_ids[father] = id
                    else:
                        father_id = self.get_id(father)
                        parents.append(father_id)
                        self.parent_child_tuples.append((father_id,id))

            self.diseases[id]['parents'] = parents


    def extract_id(self, elem):
        return elem.replace(":", "_")

    # return the proper prefix.
    def get_prefix(self,id):
        simple_id = re.match(r'^(.+?)_', id)
        if simple_id.group() in ["EFO_", "OTAR_"]:
            return "http://www.ebi.ac.uk/efo/"
        elif (simple_id.group() in 'Orphanet_'):
            return "http://www.orpha.net/ORDO/"
        else:
            return "http://purl.obolibrary.org/obo/"

    def extract_id_from_uri(self, uri):
        new_terms = []
        if isinstance(uri,str):
            uris_to_extract = [uri]
        elif isinstance(uri,list):
            uris_to_extract = self.get_array_value(uri)
        else:
            #todo: investigate to this case.
            uris_to_extract = []

        for uri_i in uris_to_extract:
            full_path=parse.urlsplit(uri_i).path
            new_terms.append(full_path.rpartition('/')[2])

        return new_terms

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

    # Check if the efo term is valid. term obsolete goes to a dedicated structure
    def is_obsolete(self,disease, disease_id):
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

    def load_type_class(self, disease, disease_id):
        if not disease["@id"].startswith('_:'):
            if disease_id == "EFO_0001422":
                print("gh")
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
            if "unionOf" in disease:
                self.class_restriction[disease["@id"]] = disease["unionOf"]["@list"]
            else:
                # Todo: check this case
                self.class_restriction[disease["@id"]] = disease["intersectionOf"]["@list"]
                print(disease)


    #
    def get_obsolete_info(self):
        for k, v in self.diseases_obsolete.items():
            if k in self.diseases:
                self.diseases[k]['obsoleteTerms'] = list(self.diseases_obsolete[k])

    def get_locationIds(self):
        for k,v in self.has_location_ids.items():
            if k in self.restriction:
                self.diseases[v]["locationIds"] = set()
                value = self.restriction[k]
                if value.startswith("_:"):
                    match = self.class_restriction[value]
                    for item in match:
                        if item.startswith("_:"):
                            if item in self.restriction:
                                self.diseases[v]["locationIds"].add(re.sub(r'^.*?:', '', self.restriction[item]))
                        else:
                            self.diseases[v]["locationIds"].add(re.sub(r'^.*?:', '', item))
                else:
                    self.diseases[v]["locationIds"].add(re.sub(r'^.*?:', '', value))


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
                            self.restriction[disease["@id"]] = disease["someValuesFrom"]

        self.get_obsolete_info()
        self.get_locationIds()

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
                del(entry["parents"])

                writer.write(entry)

    def save_diseases(self, output_filename):
        disease_filename = PIS_OUTPUT_ANNOTATIONS+'/'+output_filename
        with jsonlines.open(disease_filename, mode='w') as writer:
            for disease in self.diseases:
                # Set cannot be transform in Json. Transform into list.
                if 'locationIds' in self.diseases[disease]:
                    listValues = list(self.diseases[disease]['locationIds'])
                    self.diseases[disease]['locationIds'] = listValues

                if len(self.diseases[disease]['children']) > 0:
                    self.diseases[disease]['ontology']['leaf'] = False
                else:
                    self.diseases[disease]['ontology']['leaf'] = True

                if disease in self.all_path:
                    self.diseases[disease]['path_codes'] = self.all_path[disease]
                    self.diseases[disease]['therapeutic_codes'] = list(set(item for sublist in self.all_path[disease] for item in sublist).intersection(self.root_nodes))

                writer.write(self.diseases[disease])

        return disease_filename