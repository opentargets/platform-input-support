from platform_input_support.step.step_repository import Step


class GO(Step):
    def __init__(self):
        super().__init__()

    def run(self):
        self.start_step()

        print(self.parts)

        # manifest_step.resources.extend(Downloads('./output').exec(conf))
        # get_manifest_service().compute_checksums(manifest_step.resources)
        # if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
        #     manifest_step.status_completion = ManifestStatus.FAILED
        #     manifest_step.msg_completion = 'COULD NOT retrieve all the resources'
        # # TODO - Validation
        # if manifest_step.status_completion != ManifestStatus.FAILED:
        #     manifest_step.status_completion = ManifestStatus.COMPLETED
        #     manifest_step.msg_completion = 'The step has completed its execution'
        # logger.info('[STEP] END, GO')
