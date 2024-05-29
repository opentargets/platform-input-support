import os
import pathlib
import pytest

from platform_input_support.modules.common.YAMLReader import YAMLReader
import platform_input_support.modules.cfg as cfg
from platform_input_support.manifest.services import get_manifest_service, ManifestStatus


@pytest.fixture()
def manifest_config():
    """Create the test config and args necessary to instantiate a manifest service"""
    # setup
    yaml = YAMLReader(None).read_yaml()
    yaml.output_dir = "tests/resources"
    cfg.setup_parser()
    args = cfg.get_args()
    yield yaml, args
    # teardown
    manifest_json = pathlib.Path(yaml.output_dir).joinpath(
        pathlib.Path(yaml.config.manifest.file_name)
    )
    if manifest_json.exists():
        os.remove(manifest_json)


class TestManifestService:
    """Test manifest service class"""

    @pytest.mark.xfail(
        reason="Failing due to clashing tests using the sample global ManifestService instance"
    )
    def test_update_manifest_after_run(self, manifest_config: tuple) -> None:
        test_step = "disease"
        config, args = manifest_config
        ms = get_manifest_service(configuration=config, args=args)
        # add a failed manifest step
        disease_step = ms.get_step(test_step)
        disease_step.status_completion = ManifestStatus.FAILED
        ms.evaluate_manifest_document()
        # status should not be COMPLETED
        assert ms.manifest.status_completion != ManifestStatus.COMPLETED
        assert ms.manifest.status != ManifestStatus.COMPLETED
        ms.persist()
        # read file again to a new manifest object
        new_ms = get_manifest_service(configuration=config, args=args)
        # set all step to complete
        new_ms.manifest.steps.get(
            test_step
        ).status_completion = ManifestStatus.COMPLETED
        new_ms.evaluate_manifest_document()
        ## status shoule be COMPLETED after updating
        assert new_ms.manifest.status_completion == ManifestStatus.COMPLETED
        assert new_ms.manifest.status == ManifestStatus.COMPLETED
