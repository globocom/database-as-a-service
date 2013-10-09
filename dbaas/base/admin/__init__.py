# -*- coding:utf-8 -*-
from django.contrib import admin

from ..models import Instance, Database, Credential, Engine

from ..admin.instance import InstanceAdmin
from ..admin.database import DatabaseAdmin
from ..admin.credential import CredentialAdmin
from ..admin.engine import EngineAdmin

admin.site.register(Instance, InstanceAdmin)
admin.site.register(Database, DatabaseAdmin)
admin.site.register(Credential, CredentialAdmin)
admin.site.register(Engine, EngineAdmin)
