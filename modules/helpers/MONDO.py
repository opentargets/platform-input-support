import logging
import re
import json
import jsonlines
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS

logger = logging.getLogger(__name__)


class MONDO(object):

    def __init__(self, mondo_input):
        self.mondo_input = mondo_input
        self.mondo = {}

    def init_mondo(self, id):
        self.mondo[id] = {}
        self.mondo[id]['id'] = id
        self.mondo[id]['resource'] = 'MONDO'

    def extract_id(self, elem):
        return elem.replace(":", "_")

    def get_id(self, mondo):
        if 'id' in mondo:
            return mondo['id'].replace(":", "_")
        if '@id' in mondo:
            return re.sub(r'^.*?:', '', mondo['@id'] )
        else:
            print ("orrore")

    def set_dbXRefs(self, id, mondo):
        dbXRefs = []
        if 'hasDbXref' in mondo:
            if isinstance(mondo['hasDbXref'], str):
                dbXRefs.append(mondo['hasDbXref'])
            else:
                for ref in mondo['hasDbXref']:
                    dbXRefs.append(ref)

            self.mondo[id]['dbXRefs']= dbXRefs

    def set_obsoleted_term(self, id, mondo):
        if "hasAlternativeId" in mondo:
            obsolete = []
            if isinstance(mondo['hasAlternativeId'], str):
                obsolete.append(self.extract_id(mondo['hasAlternativeId']))
            else:
                for term in mondo['hasAlternativeId']:
                    obsolete.append(self.extract_id(term))

            self.mondo[id]['obsolete_terms'] = obsolete


    def set_label(self, id, mondo):
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

    def is_valid(self,mondo):
        if 'owl:deprecated' in mondo:
            return False
        else:
            return True

    def get_subClassOf(self,id, mondo):
        if "subClassOf" in mondo:
            classesOf = []
            if isinstance(mondo['subClassOf'], str):
                classesOf.append(re.sub(r'^.*?:', '', mondo['subClassOf'] ).replace(":", "_"))
            else:
                for term in mondo['subClassOf']:
                    classesOf.append(re.sub(r'^.*?:', '', term).replace(":", "_"))

            self.mondo[id]['subClassOf'] = classesOf

    def set_mapping(self, id, mondo):
        if 'someValuesFrom' in mondo:
            self.mondo[id]['mapping'] = re.sub(r'^.*?:', '', mondo['someValuesFrom'] ).replace(":", "_")

    def set_phenotype(self):
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
                    self.set_mapping(id,mondo)

        self.set_phenotype()


    def save_mondo(self, output_filename):
        with jsonlines.open(PIS_OUTPUT_ANNOTATIONS+'/'+output_filename, mode='w') as writer:
            for elem in self.mondo:
                writer.write(self.mondo[elem])