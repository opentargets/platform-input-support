import logging
import re
import json
import jsonlines

logger = logging.getLogger(__name__)


class HPO(object):

    def __init__(self, hpo_input):
        self.hpo_input = hpo_input
        self.hpo = {}
        self.hpo_obsolete = {}

    def init_hp(self, id):
        self.hpo[id] = {}
        self.hpo[id]['id'] = id

    def extract_id(self, elem):
        return elem.replace(":", "_")


    def get_id(self, hp):
        if 'id' in hp:
            return hp['id'].replace(":", "_")
        elif '@id' in hp:
            return re.sub(r'^.*?:', '', hp['@id'] ).replace(":", "_")
        else:
            print ("skip this id:"+ hp)

    def is_not_obsolete(self,id, hpo):
        if 'owl:deprecated' in hpo:
            return False
        return True


    def set_label(self, id, hpo):
        if 'label' in hpo:
            if isinstance(hpo['label'], str):
                self.hpo[id]['name'] = hpo['label']
            elif isinstance(hpo['label'], dict):
                self.hpo[id]['name'] = hpo['label']['@value']
            else:
                if isinstance(hpo['label'][0],str):
                    self.hpo[id]['name'] = hpo['label'][0]
                else:
                    self.hpo[id]['name'] = hpo['label'][0]['@value']

    def get_father(self, id):
        return re.sub(r'^.*?:', '', id)

    def set_parents(self, id, hpo):
        parents = []
        if 'subClassOf' in hpo:
            if isinstance(hpo['subClassOf'], str):
                parents.append(self.get_father(hpo['subClassOf']))
            else:
                for father in hpo['subClassOf']:
                    parents.append(self.get_father(father))
            self.hpo[id]['parents'] = parents

    def set_phenotypes(self, id, hpo):
        dbXRefs = []
        if 'hasDbXref' in hpo:
            if isinstance(hpo['hasDbXref'], str):
                dbXRefs.append(hpo['hasDbXref'])
            else:
                for ref in hpo['hasDbXref']:
                    dbXRefs.append(ref)

            self.hpo[id]['dbXRefs']= dbXRefs

    def set_description(self, id, hpo):
        if 'IAO_0000115' in hpo:
            if isinstance(hpo['IAO_0000115'], str):
                self.hpo[id]['description'] = hpo['IAO_0000115']
            else:
                if '@value' in hpo['IAO_0000115']:
                    self.hpo[id]['description'] = hpo['IAO_0000115']['@value']
                else:
                    self.hpo[id]['description'] = hpo['IAO_0000115'][0]


    def set_namespace(self,id, hpo):
        namespace = []
        if 'hasOBONamespace' in hpo:
            if isinstance(hpo['hasOBONamespace'], str):
                namespace.append(hpo['hasOBONamespace'])
            else:
                for ns in hpo['hasOBONamespace']:
                    if ns != 'none':
                        namespace.append(ns)
        else:
            if re.match(r'^.*?HP', id) :
                self.hpo[id]['namespace'] = namespace.append("human_phenotype")

        self.hpo[id]['namespace'] = namespace

    def set_obsoleted_term(self, id, hpo):
        if "hasAlternativeId" in hpo:
            obsolete = []
            if isinstance(hpo['hasAlternativeId'], str):
                obsolete.append(self.extract_id(hpo['hasAlternativeId']))
            else:
                for term in hpo['hasAlternativeId']:
                    obsolete.append(self.extract_id(term))

            self.hpo[id]['obsolete_terms'] = obsolete

    def generate(self):
        with open(self.hpo_input) as input:
            for line in input:
                hp = json.loads(line)
                id = self.get_id(hp)
                if self.is_not_obsolete(id,hp):
                    self.init_hp(id)
                    self.set_obsoleted_term(id, hp)
                    self.set_namespace(id, hp)
                    self.set_description(id,hp)
                    self.set_label(id, hp)
                    self.set_parents(id,hp)
                    self.set_phenotypes(id, hp)


    def save_hpo(self, output_filename):
        with jsonlines.open(output_filename, mode='w') as writer:
            for hp in self.hpo:
                writer.write(self.hpo[hp])
        return output_filename