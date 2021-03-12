from ftplib import FTP
import pandas as pd
import glob
import os
import gzip
import shutil

release = 103
url = 'ftp.ensembl.org'
path = f'/pub/release-{release}/tsv/'
filematch = '*uniprot.tsv.gz'
# All species files will be concatenated here
output_file = "species_combined.tsv"

if __name__ == "__main__":
    print("Utiltity script to get ensembl files to link orthologues to uniprot accession numbers.")
    ftp = FTP(url)
    ftp.login()
    downloaded = []
    for s in ftp.nlst(path):
        try:
            ftp.cwd(s)
            for filename in ftp.nlst(filematch):
                # if file already exists don't download it again
                if os.path.isfile(filename):
                    continue
                print(f"Downloading {filename}")
                fhandle = open(filename, 'wb')
                ftp.retrbinary('RETR ' + filename, fhandle.write)
                fhandle.close()
                downloaded.append(filename)
        except Exception as e:
            print(e)

    print("Concatenating species files.")
    # extension = 'tsv.gz'
    # downloaded = [i for i in glob.glob('*.{}'.format(extension))]
    combined_csv = pd.concat([pd.read_csv(f) for f in downloaded])
    combined_csv.to_csv(output_file, index=False, encoding='utf-8-sig')

    # with open(output_file, 'rb') as f_in:
    #     with gzip.open(output_file + '.gz', 'wb') as f_out:
    #         shutil.copyfileobj(f_in, f_out)

    print("Deleting intermediary files")
    #downloaded.append(output_file)
    for f in downloaded:
        if os.path.exists(f):
            os.remove(f)

    print("Process finished.")
