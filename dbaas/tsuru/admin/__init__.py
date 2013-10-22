# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from .. import models
from .bind import BindAdmin

admin.site.register(models.Bind, BindAdmin)
