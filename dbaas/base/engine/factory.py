from django.conf import settings
from .base import BaseEngine

from mongodb import MongoDB

class EngineFactory(object):

    @staticmethod
    def is_engine_available(name):
        return name in settings.INSTALLED_APPS

    @staticmethod
    def factory(name, node):

        engine_name = name.lower()

        # TODO: import Engines dynamically
        if engine_name == "mongodb":
            if EngineFactory.is_engine_available(engine_name):
                return MongoDB(node=node)
            else:
                raise NotImplementedError()

        assert 0, "Bad Engine Type: " + name
