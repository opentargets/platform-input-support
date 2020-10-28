from definitions import *
import os
import sys
import zipfile
import gzip
import shutil
import datetime
import binascii

def is_gzip(filename):
    with open(filename, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'

def get_lines(input_filename):
    i = 0
    if is_gzip(input_filename):
        with gzip.open(input_filename, 'rb') as f:
            for i, l in enumerate(f):
                pass
    return i+1


def get_output_dir(output_dir, default_output_dir):
    if output_dir is None:
        output_dir = default_output_dir
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except OSError:
        sys.exit('Fatal: output directory "' + output_dir + '" does not exist and cannot be created')

    return output_dir

# Init output dirs structure. Using defintiion.py vars
def init_output_dirs():
    get_output_dir(None, PIS_OUTPUT_DIR)
    get_output_dir(None, PIS_OUTPUT_ANNOTATIONS)
    get_output_dir(None, PIS_OUTPUT_EVIDENCES)
    get_output_dir(None, PIS_OUTPUT_SUBSET_EVIDENCES)
    get_output_dir(None, PIS_OUTPUT_CHEMICAL_PROBES)
    get_output_dir(None, PIS_OUTPUT_KNOWN_TARGET_SAFETY)
    get_output_dir(None, PIS_OUTPUT_TEP)
    get_output_dir(None, PIS_OUTPUT_CHEMBL_API)
    get_output_dir(None, PIS_OUTPUT_CHEMBL_ES)
    get_output_dir(None, PIS_OUTPUT_INTERACTIONS)
    get_output_dir(None, PIS_OUTPUT_ANNOTATIONS_QC)

def make_gzip(file_with_path):
    """Compress file_with_path to file_with_path.gz and return file name."""
    r_filename = file_with_path + '.gz'
    with open(file_with_path, 'rb') as f_in, gzip.open(r_filename, 'wb') as f_out:
        f_out.writelines(f_in)

    return r_filename

def make_ungzip(file_with_path):
    filename_unzip = file_with_path.replace('.gz', '').replace('.gzip', '').replace('.zip', '')
    with gzip.open(file_with_path, 'rb') as f_in:
        with open(filename_unzip, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    f_in.close()
    f_out.close()
    return filename_unzip


def make_zip(file_with_path):
    filename_zip = file_with_path+".zip"
    zf = zipfile.ZipFile(filename_zip, "w",zipfile.ZIP_DEFLATED, allowZip64 = True)
    zf.write(file_with_path)
    zf.close()
    return filename_zip


#The procedure raises an error if the zip file contains more than a file.
def make_unzip_single_file(file_with_path):
    split_filename = file_with_path.rsplit('/', 1)
    dest_filename = split_filename[1] if len(split_filename) == 2 else split_filename[0]
    output_dir = split_filename[0] if len(split_filename) == 2 else None
    filename_unzip = dest_filename.replace('.gz', '').replace('.gzip', '').replace('.zip', '')

    # Change the metadata of the file renaming the filename metadata.
    zipdata = zipfile.ZipFile(file_with_path)
    zipinfos = zipdata.infolist()
    if len(zipinfos) != 1:
        raise ValueError('Zip File contains more than a single file %s.' % file_with_path)
    zipinfos[0].filename = filename_unzip
    filename_unzip_with_path=zipdata.extract(zipinfos[0],output_dir)

    return filename_unzip_with_path


def get_output_spark_files(directory_info, filter):
    return [directory_info+'/'+file for file in os.listdir(directory_info) if file.endswith(filter)]


def replace_suffix(filename):
    suffix = datetime.datetime.today().strftime('%Y-%m-%d')
    return filename.replace('{suffix}', suffix)
