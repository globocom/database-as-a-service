# -*- coding: utf-8 -*-
import logging
from ..util.base import BaseStep

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

class TestStep3(BaseStep):
    def __unicode__(self):
        return "TestStep3"

    def do(self, workflow_dict):
        return False

    def undo(self, workflow_dict):
        return True


class TestStep4(BaseStep):
    def __unicode__(self):
        return "TestStep4"

    def do(self, workflow_dict):
        return True

    def undo(self, workflow_dict):
        raise Exception
        return False
