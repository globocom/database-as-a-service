# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.base import BaseStep


LOG = logging.getLogger(__name__)


class CheckDatabaseBinds(BaseStep):

    def __unicode__(self):
        return "Checking database acl binds..."

    def do(self, workflow_dict):
        raise Exception('Legacy Code')

    def undo(self, workflow_dict):
        raise Exception('Legacy Code')
