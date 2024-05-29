import os
import re
import gzip
import shutil
import logging
import zipfile
import pathlib
import binascii

from datetime import datetime

logger = logging.getLogger(__name__)


# NOTE Refactor this out into a helper module
def is_gzip(filename):
    """
    Check whether the given path is a gzip file

    :return: True if the given path is a gzip file, False otherwise
    """
    with open(filename, 'rb') as test_f:
        # Check for the magic number for gzip files
        return binascii.hexlify(test_f.read(2)) == b'1f8b'


# Regular expression for date and format
def date_reg_expr(sourcestr, regexpr, format):
    """
    Extract the date from a string given the date regular expression to isolate it from the rest of the string, and its
    format, for building the date object

    :param sourcestr: string to extract the date from
    :param regexpr: regular expression to use for isolating the date substring
    :param format: expected format of the date substring
    :return: the extracted date as an object or None if it was not possible
    """
    date_file = None
    re_match = re.search(regexpr, sourcestr)
    if re_match:
        try:
            date_file = datetime.strptime(re_match.group(1), format)
            if date_file.year < 2000:
                date_file = None
        except ValueError:
            # Date does not match format. No valid date found.
            date_file = None
    return date_file


# Extract any date in the format dd-mm-yyyy or yyyy-mm-dd and other sub cases.
# Return None if date are not available.
def extract_date_from_file(filename):
    """
    This method will try to extract a given file date by using different date formats, if possible

    :param filename: filename that contains a date string
    :return: the date information found in the file name or None if no date information was found
    """
    valid_date = []
    # First format to try
    valid_date.append(date_reg_expr(filename, "([0-9]{4}-[0-9]{2}-[0-9]{2})", '%Y-%m-%d'))
    valid_date.append(date_reg_expr(filename, "([0-9]{2}-[0-9]{2}-[0-9]{4})", '%d-%m-%Y'))
    if valid_date.count(None) == len(valid_date):
        # Second format to try
        # Case d-mm-yyyy or dd-m-yyyy
        valid_date.append(date_reg_expr(filename, "([0-9]{1}-[0-9]{2}-[0-9]{4})", '%d-%m-%Y'))
        valid_date.append(date_reg_expr(filename, "([0-9]{2}-[0-9]{1}-[0-9]{4})", '%d-%m-%Y'))
    if valid_date.count(None) == len(valid_date):
        # Third format to try
        # Case yyyy-m-dd or yyyy-mm-d
        valid_date.append(date_reg_expr(filename, "([0-9]{4}-[0-9]{1}-[0-9]{2})", '%Y-%m-%d'))
        valid_date.append(date_reg_expr(filename, "([0-9]{4}-[0-9]{2}-[0-9]{1})", '%Y-%m-%d'))
    # So no double dd or mm present.
    if valid_date.count(None) == len(valid_date):
        # Forth format to try
        valid_date.append(date_reg_expr(filename, "([0-9]{1}-[0-9]{1}-[0-9]{4})", '%d-%m-%Y'))
        valid_date.append(date_reg_expr(filename, "([0-9]{4}-[0-9]{1}-[0-9]{1})", '%Y-%m-%d'))
    if valid_date.count(None) != len(valid_date):
        final_date = list(filter(None, valid_date))
        if len(final_date) == 1:
            return final_date[0]
        raise ValueError("Unexpected error !!!")
    return None


def recursive_remove_folder(folder):
    """
    Remove the folder tree starting at the given folder

    :param folder: starting point for the recursive removal of files and folders
    :return: the removed folder tree path if success, None otherwise
    """
    try:
        logger.debug("Removing '{}' folder tree...".format(folder))
        shutil.rmtree(folder)
        return folder
    except Exception as e:
        logger.error("Error while deleting folder tree '{}'".format(e))
    return None


def create_folder(folder):
    """
    Create the given folder including all possible parents

    :return: the created folder
    :raise OSError: in case the folder could not be created
    """
    try:
        pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        msg = "Fatal: output directory '{}' does not exist and cannot be created. ERROR: '{}'".format(folder, e)
        logger.error(msg)
        raise
    return folder


def make_gzip(file_with_path, dest_filename=None):
    """
    Gzip compress the file at the given path, by using the highest compression level '9'

    :param file_with_path: path to the source file
    :param dest_filename: optional, path to the destination file, if missing, the path to the source file will be used
    but appending '.gz' to it
    :return: the destination file path where to the source file content has been compressed to
    """
    if dest_filename is None:
        dest_filename = file_with_path + '.gz'
    with open(file_with_path, 'rb') as f_in, gzip.open(dest_filename, 'wb') as f_out:
        # TODO Why not using shutil.copyfileobj() like for the gunzip method?
        f_out.writelines(f_in)
    return dest_filename


def make_gunzip(file_with_path):
    """
    Gzip uncompress the file at the given path, in place, into a new file path with the compressed file extension
    removed

    :param file_with_path: path to the file that will be gunzipped
    :return: the path to the uncompressed file
    """
    filename_unzip = file_with_path.replace('.gz', '').replace('.gzip', '').replace('.zip', '').replace('.bgz', '')
    with gzip.open(file_with_path, 'rb') as f_in:
        with open(filename_unzip, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return filename_unzip


def make_zip(file_with_path):
    """
    Compress the file in the given path using Zip, in place, into a new file with '.zip' extension

    :param file_with_path: source file path
    :return: path to the compressed file
    """
    filename_zip = file_with_path + ".zip"
    with zipfile.ZipFile(filename_zip, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        zf.write(file_with_path)
    return filename_zip


def extract_file_from_zip(file_to_extract_path: str, zip_file: str, output_dir: str) -> str:
    """
    Opens `zip_file` and saves `file_to_extract` to `output_dir`.

    :param file_to_extract_path: file to extract from the zip compressed file
    :param zip_file: zip compressed file where to extract the file from
    :param output_dir: destination folder for the extracted file
    """
    with zipfile.ZipFile(zip_file) as zf:
        if file_to_extract_path in zf.namelist():
            _, dst_file_name = os.path.split(file_to_extract_path)
            with open(os.path.join(output_dir, dst_file_name), "wb") as f:
                logger.debug(f"Extracting {file_to_extract_path} from {zip_file} to {f.name}")
                f.write(zf.read(file_to_extract_path))
                return f.name
    return ''


def make_unzip_single_file(file_with_path):
    """
    Unzip a given zip file that contains only one compressed file.

    :param file_with_path: path to the zip file to uncompress
    :raise ValueError: if the zip file contains more than one compressed file
    :result: the uncompressed file within the zip file
    """
    zipdata = zipfile.ZipFile(file_with_path)
    zipinfos = zipdata.infolist()
    if len(zipinfos) != 1:
        raise ValueError('Zip File contains more than a single file %s.' % file_with_path)
    zipinfos[0].filename = os.path.basename(file_with_path).replace('.gz', '').replace('.gzip', '').replace('.zip', '')
    return zipdata.extract(zipinfos[0],
                           os.path.dirname(file_with_path)
                           if os.path.dirname(file_with_path) != '' else None)


def get_output_spark_files(directory_info, filter):
    """
    Get a listing of paths to files in a given folder which file name ends in the given filter

    :param directory_info: folder to list files from
    :param filter: filter condition to get the file listing
    :return: a list of paths in the given folder which file name end matches the given filter
    """
    return [os.path.join(directory_info, file) for file in os.listdir(directory_info) if file.endswith(filter)]


def set_suffix_timestamp(filename):
    """
    Given a file name, set its suffix to the current date by replacing '{suffix}' placeholder in the name of the file

    :param filename: file name to set its suffix
    :return: the new file name with its suffix set to current date
    """
    return filename.replace('{suffix}', datetime.today().strftime('%Y-%m-%d'))
