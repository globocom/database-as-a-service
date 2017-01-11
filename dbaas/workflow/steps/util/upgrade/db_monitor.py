# -*- coding: utf-8 -*-
from util import build_context_script, exec_remote_command
from dbaas_cloudstack.models import HostAttr, CloudStackPack
from workflow.steps.util.base import BaseInstanceStep


class DBMonitorStep(BaseInstanceStep):

    def __init__(self, instance):
        super(PackStep, self).__init__(instance)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class DisableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Disabling DB Montinor..."

    def do(self):
        pass


class EnableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Enabling DB Montinor..."

    def do(self):
        pass
