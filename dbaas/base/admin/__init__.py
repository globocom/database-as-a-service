# -*- coding:utf-8 -*-
from django.contrib import admin

from base.models import Instance, Host, Environment, Database, Credential

from base.admin.instance import InstanceAdmin
from base.admin.host import HostAdmin
from base.admin.environment import EnvironmentAdmin
from base.admin.database import DatabaseAdmin
from base.admin.credential import CredentialAdmin

admin.site.register(Instance, InstanceAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Database, DatabaseAdmin)
admin.site.register(Credential, CredentialAdmin)