from platform_input_support.helpers.google import GoogleHelper
from platform_input_support.util.errors import PISError

_google_helper: GoogleHelper | None = None


def init_google_helper():
    global _google_helper  # noqa: PLW0603
    if _google_helper is None:
        _google_helper = GoogleHelper()


def google_helper():
    """Return the Google helper.

    The Google helper must be initialized explicitly by calling the
    `_init_google_helper` function before trying to access it. If it is not
    initialized, a PISError is raised.

    Returns:
        GoogleHelper: The Google helper.
    """
    if _google_helper is None:
        raise PISError('Google helper not initialized')

    assert _google_helper is not None
    return _google_helper
