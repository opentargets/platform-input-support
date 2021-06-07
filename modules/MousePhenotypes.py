import json
import logging
from datetime import datetime

from opentargets_ontologyutils.rdf_utils import OntologyClassReader
import opentargets_ontologyutils.mp

from definitions import PIS_OUTPUT_MOUSE_PHENOTYPES


class MousePhenotypes:

    def __init__(self, config_dict, output_dir=PIS_OUTPUT_MOUSE_PHENOTYPES):
        self.logger = logging.getLogger(__name__)
        self.config = config_dict
        self.mp_ontology_reader = OntologyClassReader()
        self.output_dir = output_dir
        self.suffix = datetime.today().strftime('%Y-%m-%d')

    def run(self) -> str:

        mps = {}
        mp_uri = self.config['mp_ontology']
        opentargets_ontologyutils.mp.load_mammalian_phenotype_ontology(self.mp_ontology_reader, mp_uri)

        for mp_id, label in list(self.mp_ontology_reader.current_classes.items()):

            mp_class = {"id": mp_id, "label": label}
            if mp_id not in self.mp_ontology_reader.classes_paths:
                self.logger.warning("cannot find paths for " + mp_id)
                continue
            mp_class["path"] = self.mp_ontology_reader.classes_paths[mp_id]['all']
            mp_class["path_codes"] = self.mp_ontology_reader.classes_paths[mp_id]['ids']

            mp_id_key = mp_id.split("/")[-1].replace(":", "_")
            mps[mp_id_key] = mp_class

        output_filename = self.output_dir + '/' + self.config.output_filename.replace('{suffix}', self.suffix)

        with open(output_filename, "w") as outfile:
            for entry in mps.values():
                json.dump(entry, outfile)
                outfile.write('\n')

        self.logger.info("Mouse Phenotypes output filename : %s", output_filename)

        return output_filename
