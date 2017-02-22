# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.base import BaseInstanceStep
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command
from time import sleep

LOG = logging.getLogger(__name__)


class StartAgents(BaseInstanceStep):

    def __init__(self, instance):
        super(StartAgents, self).__init__(instance)

        self.infra = self.instance.databaseinfra
        self.driver = self.infra.get_driver()
        self.host = self.instance.hostname
        self.host_attr = HostAttr.objects.get(host=self.host)

    def __unicode__(self):
        return "Starting database agents..."

    def do(self):
        sleep(30)

        for agent in self.driver.get_database_agents():
            script = '/etc/init.d/{} start'.format(agent)
            output = {}
            return_code = exec_remote_command(server=self.host.address,
                                              username=self.host_attr.vm_user,
                                              password=self.host_attr.vm_password,
                                              command=script,
                                              output=output)
            LOG.info('Running {} - Return Code: {}. Output script: {}'.format(
                     script, return_code, output))

    def undo(self):
        pass
