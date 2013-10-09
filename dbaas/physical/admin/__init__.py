# -*- coding:utf-8 -*-
from django.contrib import admin
from .. import models
from .instance import InstanceAdmin
from .engine import EngineAdmin
from .plan import PlanAdmin

admin.site.register(models.Instance, InstanceAdmin)
admin.site.register(models.Engine, EngineAdmin)
admin.site.register(models.Plan, PlanAdmin)
