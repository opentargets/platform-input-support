import os
import pathlib
import pytest

from modules.common.YAMLReader import YAMLReader
from manifest.services import get_manifest_service, ManifestService, ManifestStatus


@pytest.fixture()
def manifest_config():
    """Create the test config"""
    # setup
    yaml = YAMLReader(None).read_yaml()
    config = yaml.config.manifest
    config.output_dir = "tests/resources"
    config.gcp_bucket = None
    yield config
    # teardown
    manifest_json = pathlib.Path(config.output_dir).joinpath(
        pathlib.Path(config.file_name)
    )
    if manifest_json.exists():
        os.remove(manifest_json)


class TestManifestService:
    """Test manifest service class"""

    def test_update_manifest_after_run(self, manifest_config) -> None:
        ms = get_manifest_service(configuration=manifest_config)
        # add a failed manifest step
        disease_step = ms.get_step("disease")
        disease_step.status_completion = ManifestStatus.FAILED
        ms.manifest.status_completion = ManifestStatus.FAILED
        ms.manifest.status = ManifestStatus.FAILED
        ms.evaluate_manifest_document()
        assert ms.manifest.status_completion != ManifestStatus.COMPLETED
        assert ms.manifest.status != ManifestStatus.COMPLETED
        # persist to file
        ms.persist()
        # set all step to complete
        disease_step.status_completion = ManifestStatus.COMPLETED
        # status shoule be COMPLETE after updating
        ms.evaluate_manifest_document()
        assert ms.manifest.status_completion == ManifestStatus.COMPLETED
        assert ms.manifest.status == ManifestStatus.COMPLETED
