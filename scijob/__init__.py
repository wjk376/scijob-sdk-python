from ._client import AsyncClient, Client
from ._exceptions import *
from .__version__ import __version__

__all__ = [
    "__version__",
    "AsyncClient",
    "Client",
    "HttpRequestError",
    "GetJobResultError",
    "JobCancelledError",
    "JobStateFailedError",
    "JobStateMissingError",
    "JobStateStoppedError",
]

__locals = locals()
for __name in __all__:
    if not __name.startswith("__"):
        setattr(__locals[__name], "__module__", "scijob")  # noqa