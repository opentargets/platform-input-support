import os
from pathlib import Path

from loguru import logger
from yapsy.PluginManager import PluginManager

from platform_input_support import PIS_OUTPUT_DIR, ROOT_DIR
from platform_input_support.manifest import ManifestStatus, get_manifest_service
from platform_input_support.modules.common import create_folder, recursive_remove_folder
from platform_input_support.modules.common.google_bucket_repository import GoogleBucketResource
from platform_input_support.modules.common.utils import Utils


class RetrieveResource:
    def __init__(self, args, yaml):
        self.args = args
        self.yaml = yaml
        self._simple_plugin_manager = None
        self.__is_done_create_output_structure = False

    @property
    def output_dir(self):
        return self.args.get('output_dir', PIS_OUTPUT_DIR)

    @property
    def output_dir_prod(self):
        self.create_output_structure()
        return self.yaml.outputs.prod_dir

    @property
    def simple_plugin_manager(self):
        if self._simple_plugin_manager is None:
            self._simple_plugin_manager = PluginManager()
        return self._simple_plugin_manager

    def checks_gc_service_account(self):
        """Check that valid Google Cloud Platform credentials are present."""
        gcp_credentials = self.args.get('gcp_credentials')
        if gcp_credentials is None:
            logger.warning('Some of the steps may not work properly due the lack of permissions to access to GCS')
        # We may still have the default user credentials
        if not GoogleBucketResource.has_valid_auth_key(gcp_credentials):
            raise ValueError('Google credential is not valid!')

    def copy_to_gs(self):
        """Copy local files to the given Google Storage Bucket destination."""
        gcp_bucket = self.args.get('gcp_bucket')
        if gcp_bucket is not None:
            logger.info(f'Copying files to GCP bucket {gcp_bucket}')
            Utils(self.yaml.config, self.yaml.outputs).gsutil_multi_copy_to(gcp_bucket)
        else:
            logger.warning('No GCP Bucket details provided, THE COLLECTED DATA WILL STAY LOCAL')

    def matching_steps(self, steps, all_plugins_available):
        """Compute list of plugins that we need to run for covering the requested pipeline steps.

        :param steps: requested steps
        :param all_plugins_available: list of all the plugins available in the pipeline (their names)
        """
        lowercase_steps = {each_step.lower() for each_step in steps}
        matching_plugins = []
        for plugin in all_plugins_available:
            if plugin.lower() in lowercase_steps:
                matching_plugins.append(plugin)
                lowercase_steps.remove(plugin.lower())
        if lowercase_steps:
            logger.warning(f'Steps NOT FOUND: {lowercase_steps}')
        return matching_plugins

    def steps(self):
        """Compute the effective list of Pipeline Steps to run.

        This will take into account whether a particular list of steps was requested or not as well as the possibly
        excluded ones.
        """
        all_plugins_available_names = [plugin.name for plugin in self.simple_plugin_manager.getAllPlugins()]
        steps_requested = self.matching_steps(self.args.get('steps'), all_plugins_available_names)
        excluded_requested = self.matching_steps(self.args.get('exclude'), all_plugins_available_names)
        if len(self.args.get('steps')) == 0:
            plugins_to_run = list(set(all_plugins_available_names) - set(excluded_requested))
        else:
            plugins_to_run = list(set(steps_requested))

        logger.info(f'SELECTED Steps: {plugins_to_run}')
        return plugins_to_run

    def init_plugins(self):
        """Initialise Yapsy Plugin Manager."""
        # Tell it the default place(s) where to find plugins
        # NOTE - Should we parameterize this? The configuration file is probably the place for manipulating the pipeline
        #  stages behavior, so this could probably go somewhere else, maybe as an environment variable. On another
        #  thought, we may just want to make this a constant somewhere, probably the application itself, so its value is
        #  specified in a single place.
        self.simple_plugin_manager.setPluginPlaces([Path(ROOT_DIR) / 'platform_input_support' / 'plugins'])
        # Load all plugins
        self.simple_plugin_manager.collectPlugins()

    # noinspection PyBroadException
    def run_plugins(self):
        """Run the requested pipeline steps."""
        steps_to_execute = self.steps()
        # TODO - Refactor this for running all steps in parallel, collecting possible results as Futures, with the
        #  option of re-try on those that failed, based on the premise that they are idempotent
        for plugin_name in steps_to_execute:
            plugin = self.simple_plugin_manager.getPluginByName(plugin_name)
            plugin_configuration = self.yaml.steps[plugin_name.lower()]
            plugin_configuration['gcp_credentials'] = self.args.get('gcp_credentials')
            try:
                plugin.plugin_object.process(plugin_configuration, self.yaml.outputs, self.yaml.config)
            except Exception as e:
                logger.error(f'A problem occurred while running step {plugin_name}: {e}')
                raise

    def create_output_structure(self):
        """Prepare pipeline output folder.

        Including an area for staging results ('staging') and another one for final results ('prod').

        :param output_dir: destination path for the pipeline output filetree structure
        """
        if not self.__is_done_create_output_structure:
            logger.debug('Setting output structure')
            if self.args['force_clean']:
                recursive_remove_folder(self.output_dir)
            else:
                logger.warning('Output folder NOT CLEANED UP.')
            self.yaml.outputs.prod_dir = create_folder(os.path.join(self.output_dir, 'prod'))
            self.yaml.outputs.staging_dir = create_folder(os.path.join(self.output_dir, 'staging'))
            self.__is_done_create_output_structure = True
        logger.debug('Output structure has been created')

    def run(self):
        """Run Resource Retrieval process.

        This will:
            - prepare pipeline output folder structure
            - do some checks on provided GCP credentials
            - Run the effective pipeline steps as requested
            - And conditionally copy the results to the GCP bucket destination
        """
        manifest_service = get_manifest_service()
        try:
            self.create_output_structure()
            self.init_plugins()
            self.checks_gc_service_account()
            self.run_plugins()
        except Exception as e:
            logger.error(f'An error occurred while running the pipeline: {e}')
            manifest_service.manifest.status_completion = ManifestStatus.FAILED
            manifest_service.manifest.msg_completion = f"COULD NOT complete the data collection session due to '{e}'"

        manifest_service.evaluate_manifest_document()
        manifest_service.persist()
        self.copy_to_gs()
