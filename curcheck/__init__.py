from .dispatcher import Dispatcher
from .router import SiteRouter

try:
    # noinspection PyCompatibility
    from importlib.metadata import version
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    # <3.8 backport
    from importlib_metadata import version

try:
    __version__ = version(__name__)
except Exception:
    __version__ = None

__pyppeteer_version__ = 'v1.6.0'

__all__ = (
    "Dispatcher",
    "SiteRouter",
)
