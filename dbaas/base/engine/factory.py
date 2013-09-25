# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class EngineFactory(object):

    @staticmethod
    def is_engine_available(name):
        return name in settings.INSTALLED_APPS

    @staticmethod
    def factory(instance):

        if not instance:
            raise TypeError(_("Instance is not defined"))

        # TODO: import Engines dynamically
        if instance.engine_name.lower() == "mongodb":
            if EngineFactory.is_engine_available(instance.engine_name.lower()):
                from mongodb import MongoDB
                return MongoDB(instance=instance)
            else:
                raise NotImplementedError()

        assert 0, "Bad Engine Type: " + instance.engine_name.lower()
