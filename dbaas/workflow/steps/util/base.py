# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import python_2_unicode_compatible

LOG = logging.getLogger(__name__)


@python_2_unicode_compatible
class BaseStep(object):

    def __str__(self):
        return "I am a step"

    def do(self, workflow_dict):
        raise NotImplementedError

    def undo(self, workflow_dict):
        raise NotImplementedError


@python_2_unicode_compatible
class BaseInstanceStep(object):

    def __str__(self):
        return "I am a step"

    def __init__(self, instance):
        self.instance = instance

    @property
    def host(self):
        try:
            return self.instance.hostname
        except ObjectDoesNotExist:
            LOG.info(
                'Instance {} does not have hostname'.format(self.instance))
            return

    @property
    def environment(self):
        return self.instance.databaseinfra.environment

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class BaseInstanceStepMigration(BaseInstanceStep):

    @property
    def host(self):
        host = super(BaseInstanceStepMigration, self).host
        if not host:
            return
        return host.future_host

    @property
    def environment(self):
        environment = super(BaseInstanceStepMigration, self).environment
        return environment.migrate_environment
