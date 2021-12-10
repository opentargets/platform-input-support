from definitions import *
import os
import sys
import zipfile
import gzip
import shutil
import datetime
import binascii
import re
import logging
import pathlib

logger = logging.getLogger(__name__)


def is_gzip(filename):
    with open(filename, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'


# Regular expression for date and format
def date_reg_expr(filename, regexpr, format):
    date_file = None
    find_date_file = re.search(regexpr, filename)
    if find_date_file:
        try:
            date_file = datetime.datetime.strptime(find_date_file.group(1), format)
            if date_file.year < 2000:
                date_file = None
        except ValueError:
            # Date does not match format. No valid date found.
            date_file = None

    return date_file


# Extract any date in the format dd-mm-yyyy or yyyy-mm-dd and other sub cases.
# Return None if date are not available.
def extract_date_from_file(filename):
    valid_date = []
    valid_date.append(date_reg_expr(filename, "([0-9]{4}\-[0-9]{2}\-[0-9]{2})", '%Y-%m-%d'))
    valid_date.append(date_reg_expr(filename, "([0-9]{2}\-[0-9]{2}\-[0-9]{4})", '%d-%m-%Y'))
    if valid_date.count(None) == len(valid_date):
        # Case d-mm-yyyy or dd-m-yyyy
        valid_date.append(date_reg_expr(filename, "([0-9]{1}\-[0-9]{2}\-[0-9]{4})", '%d-%m-%Y'))
        valid_date.append(date_reg_expr(filename, "([0-9]{2}\-[0-9]{1}\-[0-9]{4})", '%d-%m-%Y'))
    if valid_date.count(None) == len(valid_date):
        # Case yyyy-m-dd or yyyy-mm-d
        valid_date.append(date_reg_expr(filename, "([0-9]{4}\-[0-9]{1}\-[0-9]{2})", '%Y-%m-%d'))
        valid_date.append(date_reg_expr(filename, "([0-9]{4}\-[0-9]{2}\-[0-9]{1})", '%Y-%m-%d'))
    # So no double dd or mm present.
    if valid_date.count(None) == len(valid_date):
        valid_date.append(date_reg_expr(filename, "([0-9]{1}\-[0-9]{1}\-[0-9]{4})", '%d-%m-%Y'))
        valid_date.append(date_reg_expr(filename, "([0-9]{4}\-[0-9]{1}\-[0-9]{1})", '%Y-%m-%d'))

    if valid_date.count(None) == len(valid_date):
        return None
    else:
        final_date = list(filter(None, valid_date))
        if len(final_date) == 1:
            return final_date[0]
        else:
            raise ValueError("Unexpected error !!!")


def remove_output_dir(output_dir):
    try:
        logger.info("Removing {} directories...".format(output_dir))
        shutil.rmtree(output_dir)
    except Exception as e:
        print('Error while deleting directory {}'.format(e))

    return output_dir


def create_output_dir(output_dir):
    try:
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    except OSError:
        sys.exit('Fatal: output directory "' + output_dir + '" does not exist and cannot be created')

    return output_dir


def make_gzip(file_with_path, dest_filename=None):
    """Compress file_with_path to file_with_path.gz and return file name."""
    if dest_filename is None:
        dest_filename = file_with_path + '.gz'
    with open(file_with_path, 'rb') as f_in, gzip.open(dest_filename, 'wb') as f_out:
        f_out.writelines(f_in)

    return dest_filename


def make_ungzip(file_with_path):
    filename_unzip = file_with_path.replace('.gz', '').replace('.gzip', '').replace('.zip', '').replace('.bgz', '')
    with gzip.open(file_with_path, 'rb') as f_in:
        with open(filename_unzip, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return filename_unzip


def make_zip(file_with_path):
    filename_zip = file_with_path + ".zip"
    zf = zipfile.ZipFile(filename_zip, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
    zf.write(file_with_path)
    zf.close()
    return filename_zip


def extract_file_from_zip(file_to_extract: str, zip_file: str, output_dir: str) -> str:
    """
    Opens `zip_file` and saves `file_to_extract` to `output_dir`.
    """
    file_to_extract_name = None
    with zipfile.ZipFile(zip_file) as zf:
        if file_to_extract in zf.namelist():
            _, tail = os.path.split(file_to_extract)
            with open(os.path.join(output_dir, tail), "wb") as f:
                logger.info(f"Extracting {file_to_extract} from {zip_file} to {f.name}")
                f.write(zf.read(file_to_extract))
            file_to_extract_name = f.name
    return file_to_extract_name


# The procedure raises an error if the zip file contains more than a file.
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
    filename_unzip_with_path = zipdata.extract(zipinfos[0], output_dir)

    return filename_unzip_with_path


def get_output_spark_files(directory_info, filter):
    return [directory_info + '/' + file for file in os.listdir(directory_info) if file.endswith(filter)]


def replace_suffix(filename):
    suffix = datetime.datetime.today().strftime('%Y-%m-%d')
    return filename.replace('{suffix}', suffix)
