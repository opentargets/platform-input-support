import simplejson as json
import shelve
import os
import dumbdbm
import tempfile
import yaml
import datetime
from opentargets_urlzsource import URLZSource
from common import make_gzip
import logging

logger = logging.getLogger(__name__)

class EvidenceSubset(object):

    def __init__(self, filename, output_dir, gs_output_dir):
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.filename_subset_evidence = filename
        self.output_dir = output_dir
        self.gs_output_dir = gs_output_dir+'/subsets'
        self.stats = {}
        self.elem_to_search = []
        self.read_subset_file()

    def replace_suffix(self, args):
        if args.suffix:
            self.suffix = args.suffix

    def set_filename(self, param_filename):
        return self.output_dir+'/'+param_filename.replace('{suffix}', self.suffix)

    def deref_multi(self,data, keys):
        return self.deref_multi(data[keys[0]], keys[1:]) \
            if keys else data

    def create_shelve(self,evidence_file, evidence_info):
        # Shelve creates a file with specific database. Using a temp file requires a workaround to open it.
        # dumbdbm creates an empty database file. In this way shelve can open it properly.
        t_filename = tempfile.NamedTemporaryFile(delete=False).name
        count = 0
        dumb_dict = dumbdbm.open(t_filename)
        shelve_out = shelve.Shelf(dict=dumb_dict, writeback=True)
        with URLZSource(evidence_file).open() as f_obj:
            for line in f_obj:
                try:
                    read_line = json.loads(line)
                    new_key = self.deref_multi(read_line, evidence_info['subset_key'])
                    new_key = new_key.replace(evidence_info['subset_prefix'],'')
                    count = count + 1
                    if shelve_out.has_key(new_key):
                        shelve_out[new_key].append(read_line)
                    else:
                        temp = []
                        temp.append(read_line)
                        shelve_out[new_key]=temp
                except Exception as e:
                    logging.info("This line is not in a JSON format. Skipped it")
        self.stats[evidence_file]['num_key'] = count
        logging.debug("File shelve created")
        return shelve_out

    def read_subset_file(self):
        with URLZSource(self.filename_subset_evidence).open() as f_obj:
            for line in f_obj:
                self.elem_to_search.append(line.rstrip('\n'))

    def create_subset_file(self,shelve_out, filename):
        path_filename, filename_attr = os.path.split(filename)
        new_filename = "subset_"+filename_attr.replace('.gz','')
        uri_to_filename = self.output_dir  + '/' + new_filename
        self.stats[filename]['ensembl'] ={}
        if os.path.exists(uri_to_filename): os.remove(uri_to_filename)
        with open(uri_to_filename, "a+") as file_subset:
            for key_elem in self.elem_to_search:
                if shelve_out.has_key(key_elem):
                    array_result = shelve_out[key_elem]
                    self.stats[filename]['ensembl'][key_elem] = str(len(array_result)) + ' entries found'
                    for elem in array_result:
                        file_subset.write(json.dumps(elem)+'\n')
                else:
                    self.stats[filename]['ensembl'][key_elem] = 'Not found'
        return uri_to_filename

    def create_stats_file(self):
        with open(self.output_dir+'/stats_subset_files.yml', 'w') as outfile:
            yaml.dump(self.stats, outfile, default_flow_style=False)

    def execute_subset(self, evidences_list):
        list_files_subset_evidence = {}
        for evidence_file in evidences_list:
            logging.info("Start process for the file {}".format(evidence_file))
            self.stats[evidence_file] = {}
            if evidences_list[evidence_file]['subset_key'] is not None:
                shelve_out = self.create_shelve(evidence_file,evidences_list[evidence_file])
                subset_file = self.create_subset_file(shelve_out,evidence_file)
                filename_zip = make_gzip(subset_file)
                list_files_subset_evidence[filename_zip] = {'resource': 'subset_evidence', 'gs_output_dir': self.gs_output_dir}
                self.stats[evidence_file]['filename'] = filename_zip
                logging.info("File {} has been created".format(filename_zip))
            else:
                self.stats[evidence_file]['filename'] = "The file {} won't have subset evidence file.".format(evidence_file)
                logger.info("The file {} won't have subset evidence file.".format(evidence_file))

        return list_files_subset_evidence

