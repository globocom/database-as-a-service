# -*- coding: utf-8 -*-
import logging
from ...base import BaseStep

LOG = logging.getLogger(__name__)


class TestStep1(BaseStep):
    def __unicode__(self):
        return "TestStep1"

    def do(self, workflow_dict):
        return True

    def undo(self, workflow_dict):
        return True


class TestStep2(BaseStep):
    def __unicode__(self):
        return "TestStep2"

    def do(self, workflow_dict):
        return True

    def undo(self, workflow_dict):
        return True
