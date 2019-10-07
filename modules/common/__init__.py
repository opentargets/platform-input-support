import os, sys
import zipfile
import gzip
import shutil
GZIP_MAGIC_NUMBER = "1f8b"

def is_gzip(filename):
    open_file = open(filename)
    return open_file.read(2).encode("hex") == GZIP_MAGIC_NUMBER


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


def make_gzip(file_with_path):
    r_filename = file_with_path + '.gz'
    with open(file_with_path, 'rb') as f_in, gzip.open(r_filename, 'wb') as f_out:
        f_out.writelines(f_in)

    return r_filename

def make_ungzip(file_with_path):
    filename_unzip = file_with_path.replace('.gz', '').replace('.gzip', '').replace('.zip', '')
    with gzip.open(file_with_path, 'rb') as f_in:
        with open(filename_unzip, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return filename_unzip


def make_zip(file_with_path):
    filename_zip = file_with_path+".zip"
    zf = zipfile.ZipFile(filename_zip, "w",zipfile.ZIP_DEFLATED, allowZip64 = True)
    zf.write(file_with_path)
    zf.close()
    return filename_zip


