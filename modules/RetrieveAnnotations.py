import sys

# Custom modules
import modules.cfg as cfg
from modules.DownloadResource import DownloadResource
from definitions import ROOT_DIR, OT_OUTPUT_DIR

def main():
    cfg.setup_parser()
    args = cfg.get_args()
    input_file = cfg.get_input_file(args.input_file, ROOT_DIR+'/annotations_input.csv')
    output_dir = cfg.get_output_dir(args.output_dir, OT_OUTPUT_DIR)
    for file_to_download in cfg.get_list_of_file_download(input_file):
        download = DownloadResource(output_dir)
        download.replace_suffix(args)
        if args.thread:
            handle = download.execute_download_threaded(file_to_download)
        else:
            handle = download.execute_download(file_to_download)


if __name__ == '__main__':
    sys.exit(main())