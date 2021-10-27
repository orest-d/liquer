import warnings

print("WARNING: liquer.blueprint is deprecated, use liquer.server.blueprint")
warnings.warn(
    "liquer.blueprint is deprecated, use liquer.server.blueprint",
    DeprecationWarning,
    stacklevel=2,
)
from liquer.server.blueprint import *
