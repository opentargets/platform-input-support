import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
PIS_OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
PIS_OUTPUT_ANNOTATIONS = os.path.join(PIS_OUTPUT_DIR, 'annotation-files')
PIS_OUTPUT_EVIDENCES = os.path.join(PIS_OUTPUT_DIR, 'evidence-files')
PIS_OUTPUT_SUBSET_EVIDENCES = os.path.join(PIS_OUTPUT_EVIDENCES, 'subsets')
PIS_OUTPUT_CHEMICAL_PROBES = os.path.join(PIS_OUTPUT_ANNOTATIONS, 'chemical_probes_tsv')
PIS_OUTPUT_KNOWN_TARGET_SAFETY = os.path.join(PIS_OUTPUT_ANNOTATIONS, 'known_target_safety')
PIS_OUTPUT_TEP= os.path.join(PIS_OUTPUT_ANNOTATIONS, 'tep')
PIS_OUTPUT_CHEMBL_API = os.path.join(PIS_OUTPUT_ANNOTATIONS, 'ChEMBL_API')
PIS_OUTPUT_HOMOLOGY = os.path.join(PIS_OUTPUT_ANNOTATIONS, 'homology')
PIS_OUTPUT_OTNETWORK= os.path.join(PIS_OUTPUT_ANNOTATIONS, 'otnetwork')
PIS_EVIDENCES_STATS_FILE = os.path.join(PIS_OUTPUT_DIR, 'stats_evidence_files.csv')
PIS_OUTPUT_ANNOTATIONS_QC = os.path.join(PIS_OUTPUT_DIR, 'qc')
GOOGLE_STORAGE_URI= 'https://storage.googleapis.com/'
# CONFIG = os.path.join(ROOT_DIR, 'config.yaml')  # Add later for default config file