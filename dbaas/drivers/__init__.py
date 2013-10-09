from .base import *  # NOQA
from .factory import *  # NOQA

def factory_for(*args, **kwargs):
    return DriverFactory.factory(*args, **kwargs)
