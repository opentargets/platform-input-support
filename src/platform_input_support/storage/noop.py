"""No-op storage helper module."""

from pathlib import Path

from platform_input_support.helpers import RemoteStorage
from platform_input_support.util.errors import NotFoundError


class NoopStorage(RemoteStorage):
    """No-op storage helper class.

    This class implements the RemoteStorage interface but does not perform any
    operations. It is used when the platform input support tool is run locally.
    """

    def check(self, uri: str) -> bool:
        """Check if a file exists."""
        return False

    def stat(self, uri: str) -> dict:
        """Get metadata for a file."""
        raise NotFoundError(uri)

    def list(self, uri: str, pattern: str | None = None) -> list[str]:
        """List files."""
        raise NotFoundError(uri)

    def download_to_file(self, uri: str, dst: Path) -> int:
        """Download a file to the local filesystem."""
        raise NotFoundError(uri)

    def download_to_string(self, uri: str) -> tuple[str, int]:
        """Download a file and return its contents as a string."""
        raise NotFoundError(uri)

    def upload(self, src: Path, uri: str, revision: int | None = None) -> int:
        """Upload a file."""
        return 0

    def get_session(self) -> None:
        """Return a session for making requests."""
        return None
