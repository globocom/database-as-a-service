# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.contrib.auth.models import User, Group

from ..models import Configuration

from .configuration import ConfigurationAdmin


admin.site.register(Configuration, ConfigurationAdmin)
