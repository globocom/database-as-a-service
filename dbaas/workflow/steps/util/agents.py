# -*- coding: utf-8 -*-
import logging
from base import BaseInstanceStep
from database import CheckIsUp, CheckIsDown

LOG = logging.getLogger(__name__)


class AgentsStep(BaseInstanceStep):
    pass

class Start(AgentsStep):

    def __unicode__(self):
        return "Starting database agents..."

    def do(self):
        CheckIsUp(self.instance)
        self.driver.start_agents(self.host)

    def undo(self):
        Stop(self.instance).do()


class Stop(AgentsStep):

    def __unicode__(self):
        return "Stopping database agents..."

    def do(self):
        CheckIsDown(self.instance)
        self.driver.stop_agents(self.host)

    def undo(self):
        Start(self.instance).do()
