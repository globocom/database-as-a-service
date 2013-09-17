# -*- coding:utf-8 -*-
from django.contrib import admin
from base.models import Instance
from base.admin.instance import InstanceAdmin

admin.site.register(Instance, InstanceAdmin)