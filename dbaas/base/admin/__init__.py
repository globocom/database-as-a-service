# -*- coding:utf-8 -*-
from django.contrib import admin
from base.models import Instance, Host
from base.admin.instance import InstanceAdmin
from base.admin.host import HostAdmin

admin.site.register(Instance, InstanceAdmin)
admin.site.register(Host, HostAdmin)