from platform_input_support.helpers import google_helper
from platform_input_support.manifest.manifest import Manifest


def test_upload_success_on_first_tray(monkeypatch):
    manifest = Manifest()

    monkeypatch.setattr(manifest._init_manifest, lambda: None)
    monkeypatch.setattr(google_helper(), 'upload_safe', lambda: None)

    manifest.upload()
    assert manifest.generation == 1
