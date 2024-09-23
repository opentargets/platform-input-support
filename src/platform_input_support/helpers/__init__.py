"""Helpers are common utilities used throughout the application."""

from platform_input_support.helpers.google import GoogleHelper
from platform_input_support.util.errors import PISError

_google_helper: GoogleHelper | None = None


def init_google_helper():
    """Initialize the Google helper."""
    global _google_helper  # noqa: PLW0603
    if _google_helper is None:
        _google_helper = GoogleHelper()


def google_helper():
    """Return the Google helper.

    The Google helper must be initialized explicitly by calling :func:`init_google_helper`
    before trying to access it. If it is not initialized, a PISError is raised.

    :return: The Google helper.
    :rtype: GoogleHelper
    :raises PISError: If the Google helper is not initialized.
    """
    if _google_helper is None:
        raise PISError('Google helper not initialized')

    assert _google_helper is not None
    return _google_helper
