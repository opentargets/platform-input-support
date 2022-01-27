import os
import logging
from modules.common.GoogleBucketResource import GoogleBucketResource
from modules.common.Utils import Utils
from modules.common import create_output_dir, recursive_remove_folder
from yapsy.PluginManager import PluginManager
from definitions import PIS_OUTPUT_DIR

logger = logging.getLogger(__name__)


class RetrieveResource(object):

    def __init__(self, args, yaml):
        self.simplePluginManager = PluginManager()
        self.args = args
        self.output_dir = args.output_dir if args.output_dir is not None else PIS_OUTPUT_DIR
        self.yaml = yaml

    def checks_gc_service_account(self):
        """
        Check that valid Google Cloud Platform credentials are present
        """
        if self.args.google_credential_key is None:
            logger.warning("Some of the steps might be not work properly due the lack of permissions to access to GCS. "
                        "Eg. Evidence")
        # We may still have the default user credentials
        if not GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key):
            raise ValueError("Google credential is not valid!")

    def copy_to_gs(self):
        """
        Copy local files to the given Google Storage Bucket destination
        """
        if self.args.google_bucket is not None:
            Utils(self.yaml.config, self.yaml.outputs).gsutil_multi_copy_to(self.args.google_bucket)
        else:
            logger.error("Destination bucket info missing")

    def matching_steps(self, steps, all_plugins_available):
        """
        This function finds out the list of plugins that we need to run for covering the requested pipeline steps.

        :param steps: requested steps
        :param all_plugins_available: list of all the plugins available in the pipeline
        """
        lowercase_steps = set(each_step.lower() for each_step in steps)
        matching_plugins = []
        for plugin in all_plugins_available:
            if plugin.lower() in lowercase_steps:
                matching_plugins.append(plugin)
                lowercase_steps.remove(plugin.lower())

        logger.info("Steps not found:\n" + ','.join(lowercase_steps))
        return matching_plugins

    def steps(self):
        """
        Compute the effective list of Pipeline Steps to run. This will take into account whether a particular list of
        steps was requested or not as well as the possibly excluded ones
        """
        steps_requested = self.matching_steps(self.args.steps, self.simplePluginManager.getAllPlugins())
        excluded_requested = self.matching_steps(self.args.exclude, self.simplePluginManager.getAllPlugins())
        if len(self.args.steps) == 0:
            plugins_to_run = list(set(self.simplePluginManager.getAllPlugins()) - set(excluded_requested))
        else:
            plugins_to_run = list(set(steps_requested))

        logger.info("Steps selected:\n" + ','.join(plugins_to_run))
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
        self.simplePluginManager.setPluginPlaces(["plugins"])
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
            try:
                plugin.plugin_object.process(self.yaml[plugin_name.lower()], self.yaml.outputs, self.yaml.config)
            except Exception as e:
                logger.error("A problem occurred while running step '{}'".format(plugin_name))
                logger.error(e)

    def create_output_structure(self, output_dir):
        """
        Prepare pipeline output folder including an area for staging results ('staging') and another one for final
        results ('prod').

        :param output_dir: destination path for the pipeline output filetree structure
        """
        if self.args.force_clean:
            recursive_remove_folder(output_dir)
        else:
            logger.info("Warning: Output not deleted.")
        self.yaml.outputs.prod_dir = create_output_dir(os.path.join(output_dir, 'prod'))
        self.yaml.outputs.staging_dir = create_output_dir(os.path.join(output_dir, 'staging'))

    def run(self):
        """
        Run Resource Retrieval process.

        This will:
            - prepare pipeline output folder structure
            - do some checks on provided GCP credentials
            - Run the effective pipeline steps as requested
            - And conditionally copy the results to the GCP bucket destination
        """
        self.create_output_structure(self.output_dir)
        self.init_plugins()
        self.checks_gc_service_account()
        self.run_plugins()
        self.copy_to_gs()
