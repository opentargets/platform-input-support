#Custom modules
import logging.config

# Custom modules
import modules.cfg as cfg
from modules.GoogleBucketResource import GoogleBucketResource
from modules.common.YAMLReader import YAMLReader
from modules.RetrieveResource import RetrieveResource

logger = logging.getLogger(__name__)

def get_list_steps_on_request(list_steps_requested, keys_list):
    if list_steps_requested:
        list_steps='\n\t'.join(keys_list)
        list_steps='List of steps available:\n\t'+list_steps
        print(list_steps)
        exit(0)

def main():
    cfg.setup_parser()
    args = cfg.get_args()
    yaml = YAMLReader()
    yaml_dict = yaml.read_yaml()
    get_list_steps_on_request(args.list_steps, yaml.get_list_keys())
    cfg.set_up_logging(args)

    #--gkey and --google_bucket are mandatory for the google storage access. Both keys must be parameters or none.
    GoogleBucketResource.has_google_parameters(args.google_credential_key, args.google_bucket)
    resources = RetrieveResource(args, yaml_dict, yaml_dict.data_pipeline_schema)
    resources.run()


if __name__ == '__main__':
    main()
