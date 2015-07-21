# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from .. import models
from .project import ProjectAdmin
from .database import DatabaseAdmin

admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Database, DatabaseAdmin)
