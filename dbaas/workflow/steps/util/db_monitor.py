# -*- coding: utf-8 -*-
from dbaas_dbmonitor.provider import DBMonitorProvider
from workflow.steps.util.base import BaseInstanceStep


class DBMonitorStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DBMonitorStep, self).__init__(instance)
        self.provider = DBMonitorProvider()

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class DisableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Disabling DB Monitor..."

    def do(self):
        self.provider.disabled_dbmonitor_monitoring_instance(self.instance)


class EnableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Enabling DB Monitor..."

    def do(self):
        self.provider.enabled_dbmonitor_monitoring_instance(self.instance)


class CreateMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Creating DB Monitor..."

    def do(self):
        instance_number = self.instance.databaseinfra.last_vm_created
        self.provider.create_dbmonitor_instance_monitoring(self.instance, instance_number)

    def undo(self):
        DisableMonitoring(self.instance).do()
