import logging
from modules.common.GoogleBucketResource import GoogleBucketResource
from modules.common.Utils import Utils
from modules.common import create_output_dir, remove_output_dir
from yapsy.PluginManager import PluginManager
from definitions import PIS_OUTPUT_DIR

logger = logging.getLogger(__name__)


class RetrieveResource(object):

    def __init__(self, args, yaml):
        self.simplePluginManager = PluginManager()
        self.args = args
        self.output_dir = args.output_dir if args.output_dir is not None else PIS_OUTPUT_DIR
        self.yaml = yaml

    # Warning the user about the gc credential needs for access to GC itself
    def checks_gc_service_account(self):
        if self.args.google_credential_key is None:
            logger.info("Some of the steps might be not work properly due the lack of permissions to access to GCS. "
                        "Eg. Evidence")
        else:
            GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)

    # Copy the local files to the Google Storage
    def copy_to_gs(self):
        if self.args.google_bucket is not None:
            Utils(self.yaml.config, self.yaml.outputs).gsutil_multi_copy_to(self.args.google_bucket)
        else:
            logger.error("Destination bucket info missing")

    # This function normalise the input inserted by the user. Lower and Upper cases can break the code if
    # not managed. Eg. SO/so/So -> SO Plugin
    def normalise_steps(self, steps, all_plugins_available):
        normalise_steps = []
        lowercase_steps = [each_step.lower() for each_step in steps]
        for plugin in all_plugins_available:
            if plugin.lower() in lowercase_steps:
                normalise_steps.append(plugin)
                lowercase_steps.remove(plugin.lower())

        logger.info("Steps not found:\n" + ','.join(lowercase_steps))
        return normalise_steps

    # Extract and check the steps to run
    def steps(self):
        all_plugins_available = []
        for plugin in self.simplePluginManager.getAllPlugins():
            all_plugins_available.append(plugin.name)
        steps_requested = self.normalise_steps(self.args.steps, all_plugins_available)
        excluded_requested = self.normalise_steps(self.args.exclude, all_plugins_available)
        if len(self.args.steps) == 0:
            plugin_order = list(set(all_plugins_available) - set(excluded_requested))
        else:
            plugin_order = list(set(steps_requested))

        logger.info("Steps selected:\n" + ','.join(plugin_order))
        return plugin_order

    # Init yapsy plugin manager
    def init_plugins(self):
        # Tell it the default place(s) where to find plugins
        self.simplePluginManager.setPluginPlaces(["plugins"])
        # Load all plugins
        self.simplePluginManager.collectPlugins()

    # noinspection PyBroadException
    # Given a list of steps to run, this procedure executes the selected plugins/step
    def run_plugins(self):
        steps_to_execute = self.steps()
        for plugin_name in steps_to_execute:
            plugin = self.simplePluginManager.getPluginByName(plugin_name)
            try:
                plugin.plugin_object.process(self.yaml[plugin_name.lower()], self.yaml.outputs, self.yaml.config)
            except Exception as e:
                logger.info("WARNING Plugin not available {}".format(plugin_name))
                logger.info(e)

    def create_output_structure(self, output_dir):
        """By default the directories prod and staging are created"""
        remove_output_dir(output_dir) if self.args.force_clean else logger.info("Warning: Output not deleted.")
        self.yaml.outputs.prod_dir = create_output_dir(output_dir + '/prod')
        self.yaml.outputs.staging_dir = create_output_dir(output_dir + '/staging')

    # Retrieve the resources requested.
    def run(self):
        self.create_output_structure(self.output_dir)
        self.init_plugins()
        self.checks_gc_service_account()
        self.run_plugins()
        self.copy_to_gs()
