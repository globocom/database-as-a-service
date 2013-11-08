# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging


LOG = logging.getLogger(__name__)


class TeamAdmin(admin.ModelAdmin):

    filter_horizontal = ['permissions']

    def queryset(self, request):
        return self.model.objects.exclude(name__startswith="role")
