# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from .. import models
from .analyze import AnalyzeRepositoryAdmin

admin.site.register(models.AnalyzeRepository, AnalyzeRepositoryAdmin)
