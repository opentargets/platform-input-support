import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
PIS_OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
PIS_OUTPUT_ANNOTATIONS = os.path.join(PIS_OUTPUT_DIR, 'annotations_files')
PIS_OUTPUT_EVIDENCES = os.path.join(PIS_OUTPUT_DIR, 'evidences_files')
PIS_OUTPUT_CHEMICAL_PROBES = os.path.join(PIS_OUTPUT_ANNOTATIONS, 'chemical_probes_tsv')
PIS_OUTPUT_CHEMBL_API = os.path.join(PIS_OUTPUT_ANNOTATIONS, 'ChEMBL_API')
# CONFIG = os.path.join(ROOT_DIR, 'config.yaml')  # Add later for default config file