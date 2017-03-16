# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.base import BaseInstanceStep
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command
from ..database import CheckIsUp
from time import sleep

LOG = logging.getLogger(__name__)


class Start(BaseInstanceStep):

    def __init__(self, instance):
        super(Start, self).__init__(instance)

        self.infra = self.instance.databaseinfra
        self.driver = self.infra.get_driver()
        self.host = self.instance.hostname

    def __unicode__(self):
        return "Starting database agents..."

    def do(self):
        CheckIsUp(self.instance)
        self.driver.start_agents(self.host)

    def undo(self):
        pass
