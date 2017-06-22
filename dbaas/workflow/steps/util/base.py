# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible


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

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError
