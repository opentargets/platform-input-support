import os
import logging
from platform_input_support.modules.common.Utils import Utils
from platform_input_support import ROOT_DIR, PIS_OUTPUT_DIR
from yapsy.PluginManager import PluginManager
from platform_input_support.manifest import get_manifest_service, ManifestStatus
from platform_input_support.modules.common import create_folder, recursive_remove_folder
from platform_input_support.modules.common.GoogleBucketResource import GoogleBucketResource
from pathlib import Path

logger = logging.getLogger(__name__)


class RetrieveResource(object):
    def __init__(self, args, yaml):
        self.args = args
        self.yaml = yaml
        self._simplePluginManager = None
        self.__is_done_create_output_structure = False

    @property
    def output_dir(self):
        if self.args.output_dir is not None:
            return self.args.output_dir
        return PIS_OUTPUT_DIR

    @property
    def output_dir_prod(self):
        self.create_output_structure()
        return self.yaml.outputs.prod_dir

    @property
    def simplePluginManager(self):
        if self._simplePluginManager is None:
            self._simplePluginManager = PluginManager()
        return self._simplePluginManager

    def checks_gc_service_account(self):
        """
        Check that valid Google Cloud Platform credentials are present
        """
        if self.args.gcp_credentials is None:
            logger.warning(
                "Some of the steps might be not work properly due the lack of permissions to access to GCS. "
                "Eg. Evidence"
            )
        # We may still have the default user credentials
        if not GoogleBucketResource.has_valid_auth_key(self.args.gcp_credentials):
            raise ValueError("Google credential is not valid!")

    def copy_to_gs(self):
        """
        Copy local files to the given Google Storage Bucket destination
        """
        if self.args.gcp_bucket is not None:
            logger.info(f"Copying files to GCP bucket '{self.args.gcp_bucket}'")
            Utils(self.yaml.config, self.yaml.outputs).gsutil_multi_copy_to(
                self.args.gcp_bucket
            )
        else:
            logger.warning(
                "No GCP Bucket details provided, THE COLLECTED DATA WILL STAY LOCAL"
            )

    def matching_steps(self, steps, all_plugins_available):
        """
        This function finds out the list of plugins that we need to run for covering the requested pipeline steps.

        :param steps: requested steps
        :param all_plugins_available: list of all the plugins available in the pipeline (their names)
        """
        lowercase_steps = set(each_step.lower() for each_step in steps)
        matching_plugins = []
        for plugin in all_plugins_available:
            if plugin.lower() in lowercase_steps:
                matching_plugins.append(plugin)
                lowercase_steps.remove(plugin.lower())
        if lowercase_steps: 
            logger.warning("Steps NOT FOUND:\n" + ",".join(lowercase_steps))
        return matching_plugins

    def steps(self):
        """
        Compute the effective list of Pipeline Steps to run. This will take into account whether a particular list of
        steps was requested or not as well as the possibly excluded ones
        """
        all_plugins_available_names = [
            plugin.name for plugin in self.simplePluginManager.getAllPlugins()
        ]
        steps_requested = self.matching_steps(
            self.args.steps, all_plugins_available_names
        )
        excluded_requested = self.matching_steps(
            self.args.exclude, all_plugins_available_names
        )
        if len(self.args.steps) == 0:
            plugins_to_run = list(
                set(all_plugins_available_names) - set(excluded_requested)
            )
        else:
            plugins_to_run = list(set(steps_requested))

        logger.info("SELECTED Steps:\n" + ",".join(plugins_to_run))
        return plugins_to_run

    def init_plugins(self):
        """
        Initialise Yapsy Plugin Manager
        """
        # Tell it the default place(s) where to find plugins
        # NOTE - Should we parameterize this? The configuration file is probably the place for manipulating the pipeline
        #  stages behavior, so this could probably go somewhere else, maybe as an environment variable. On another
        #  thought, we may just want to make this a constant somewhere, probably the application itself, so its value is
        #  specified in a single place.
        # Turn the volume down for the yapsy logger
        logger_yapsy = logging.getLogger("yapsy")
        logger_yapsy.setLevel(logging.INFO)
        self.simplePluginManager.setPluginPlaces([Path(ROOT_DIR) / 'platform_input_support' / 'plugins'])
        # Load all plugins
        self.simplePluginManager.collectPlugins()

    # noinspection PyBroadException
    def run_plugins(self):
        """
        Run the requested pipeline steps
        """
        steps_to_execute = self.steps()
        # TODO - Refactor this for running all steps in parallel, collecting possible results as Futures, with the
        #  option of re-try on those that failed, based on the premise that they are idempotent
        for plugin_name in steps_to_execute:
            plugin = self.simplePluginManager.getPluginByName(plugin_name)
            plugin_configuration = self.yaml[plugin_name.lower()]
            plugin_configuration["gcp_credentials"] = self.args.gcp_credentials
            try:
                plugin.plugin_object.process(
                    plugin_configuration, self.yaml.outputs, self.yaml.config
                )
            except Exception as e:
                logger.error(
                    "A problem occurred while running step '{}'".format(plugin_name)
                )
                logger.error(e)
                raise

    def create_output_structure(self):
        """
        Prepare pipeline output folder including an area for staging results ('staging') and another one for final
        results ('prod').

        :param output_dir: destination path for the pipeline output filetree structure
        """
        if not self.__is_done_create_output_structure:
            logger.debug(f"Setting output structure")
            if self.args.force_clean:
                recursive_remove_folder(self.output_dir)
            else:
                logger.warning("Output folder NOT CLEANED UP.")
            self.yaml.outputs.prod_dir = create_folder(
                os.path.join(self.output_dir, "prod")
            )
            self.yaml.outputs.staging_dir = create_folder(
                os.path.join(self.output_dir, "staging")
            )
            self.__is_done_create_output_structure = True
        logger.debug(f"Output structure has been created")

    def run(self):
        """
        Run Resource Retrieval process.

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
            manifest_service.manifest.status_completion = ManifestStatus.FAILED
            manifest_service.manifest.msg_completion = (
                f"COULD NOT complete the data collection session due to '{e}'"
            )
        manifest_service.evaluate_manifest_document()
        manifest_service.persist()
        self.copy_to_gs()
