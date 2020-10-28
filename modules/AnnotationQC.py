import pandas as pd
import numpy as np
import logging
import re
from .common import is_gzip, make_ungzip
from .GoogleBucketResource import GoogleBucketResource

logger = logging.getLogger(__name__)

class AnnotationQC(object):

    def __init__(self, yaml_info, list_files_downloaded, output_dir):
        self.annonations_qc = yaml_info
        self.output_dir = output_dir
        self.gs_output_dir = yaml_info.gs_output_dir+'/qc_annotations'
        self.gs_resource = self.init_gs_resource(yaml_info)
        self.gs_files = self.init_gs_files()
        self.local_files = list_files_downloaded


    def init_gs_resource(self, yaml_info):
        params = GoogleBucketResource.get_bucket_and_path(yaml_info.release_to_compare)
        google_resource = GoogleBucketResource(bucket_name=params)
        return google_resource

    def init_gs_files(self):
        list_files = list(self.gs_resource.list_blobs_object_path().keys())
        return list_files

    # Download the file from gs (previous file version)
    def download_previous_version_from_gs(self,filename_regular_expression, qc_filename):
        filename_downloded = None
        r = re.compile(filename_regular_expression)
        found_file = list(filter(r.match, self.gs_files))  # Read Note
        if len(found_file) == 1:
            split_filename = found_file[0].rsplit('/', 1)
            dest_filename = split_filename[1] if len(split_filename) == 2 else split_filename[0]
            filename_downloded = self.gs_resource.download_file(found_file[0],self.output_dir+'/'+dest_filename)
            if is_gzip(filename_downloded):
                # swap the name with the unzipped file
                filename_downloded = make_ungzip(filename_downloded)

        return filename_downloded

    def find_local_file(self, filename_regular_expression):
        filename = None
        r = re.compile(filename_regular_expression)
        found_file = list(filter(r.match, self.local_files))  # Read Note
        if len(found_file) == 1:
            filename = found_file[0]
            if is_gzip(filename):
                # swap the name with the unzipped file
                filename = make_ungzip(filename)

        return filename


    def compare_files(self, datatype_entry, new, old):
        out_type = datatype_entry.out_type
        keycols = datatype_entry.keycols
        datatype = datatype_entry.datatype
        out_prefix = datatype_entry.out_prefix
        output_filename = ''
        if out_type == 'summary':

            # get column names (from both files, since some may be new or removed)
            cols = list(new.columns)
            extra = [x for x in list(old.columns) if x not in cols]
            cols.extend(extra)
            # remove key columns from list
            cols = [x for x in cols if x not in keycols]

            merged = pd.merge(old, new, how='outer', on=keycols, left_on=None, right_on=None,
                              left_index=False, right_index=False, sort=True,
                              suffixes=('_old', '_new'), copy=True, indicator=False,
                              validate=None)
            merged = merged.set_index(keycols)
            if datatype == 'tractability':
                merged = merged.replace(r'(^\s*$|^0$)', np.nan, regex=True)
            else:
                merged = merged.replace(r'(^\s*$)', np.nan, regex=True)

            dfindex = ['key:{}'.format("/".join(keycols))]
            dfindex.extend(cols)
            new = new.set_index(keycols)
            old = old.set_index(keycols)
            newindex = list(new.index)
            oldindex = list(old.index)

            same = [len([x for x in newindex if x in oldindex])]
            gain = [len([x for x in newindex if x not in oldindex])]
            loss = [len([x for x in oldindex if x not in newindex])]
            change = ['N/A']

            for col in cols:

                oldcol = '{}_old'.format(col)
                newcol = '{}_new'.format(col)

                # column name common in both files
                if oldcol in list(merged.columns) and newcol in list(merged.columns):
                    same.append(sum(((merged[oldcol].isna()) & (merged[newcol].isna()))
                                    | (merged[oldcol] == merged[newcol])))
                    gain.append(sum((merged[oldcol].isna()) & (merged[newcol].notna())))
                    loss.append(sum((merged[oldcol].notna()) & (merged[newcol].isna())))
                    change.append(sum((merged[oldcol].notna()) & (merged[newcol].notna())
                                      & (merged[oldcol] != merged[newcol])))
                    # column is new
                elif col in list(new.columns):
                    same.append(0)
                    gain.append(len(newindex))
                    loss.append(0)
                    change.append(0)

                # column removed in new file
                else:
                    same.append(0)
                    gain.append(0)
                    loss.append(len(oldindex))
                    change.append(0)

            data = {'Same': same, 'Gain': gain, 'Loss': loss, 'Change': change}
            df = pd.DataFrame(data, index=dfindex)
            df.to_csv('{}_summary.csv'.format(self.output_dir+'/'+out_prefix), index=True)
            output_filename = '{}_summary.csv'.format(self.output_dir+'/'+out_prefix)
        elif out_type == 'details':

            conc = pd.concat([new, old], axis=0, join='inner')
            conc = conc.drop_duplicates(keep=False)

            cols = list(conc.columns)
            cols = [x for x in cols if x not in keycols]

            collect = conc.groupby(keycols)[cols[0]].apply(lambda x: ' / '.join(x.astype(str)))
            for col in cols[1:]:
                agg = conc.groupby(keycols)[col].apply(lambda x: ' / '.join(x.astype(str)))
                collect = pd.concat([collect, agg], axis=1)
            collect.to_csv('{}_details.csv'.format(self.output_dir+'/'+ out_prefix), index=True)
            output_filename = '{}_details.csv'.format(self.output_dir+'/'+ out_prefix)
        return output_filename

    def compare_file_data(self, datatype_entry):
        output_filename = None
        try:
            previous_file = self.download_previous_version_from_gs(datatype_entry.filename_regular_expression, datatype_entry.datatype)
            current_file = self.find_local_file(datatype_entry.filename_regular_expression)
            # Test that both file exist
            if (previous_file is not None) and (current_file is not None):
                new = pd.read_csv(current_file, sep=datatype_entry.separator, dtype=object)
                old = pd.read_csv(previous_file, sep=datatype_entry.separator, dtype=object)

            output_filename = self.compare_files(datatype_entry,  new, old)
        except Exception as e:
            print('Warning: {} QC not available'.format(datatype_entry.datatype))
        return output_filename

    def execute(self):
        list_files_downloaded = {}
        for datatype_entry in self.annonations_qc.list_datatypes:
            output_filename = self.compare_file_data(datatype_entry)
            if output_filename is not None:
                list_files_downloaded[output_filename] = {'resource': 'qc_'+datatype_entry.datatype,
                                                          'gs_output_dir': self.gs_output_dir}
        return list_files_downloaded