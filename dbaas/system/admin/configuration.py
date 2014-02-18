# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging


LOG = logging.getLogger(__name__)


class ConfigurationAdmin(admin.ModelAdmin):

    list_display = ["name", "value", "description"]
    search_fields = ("name",)

