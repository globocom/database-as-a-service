# -*- coding:utf-8 -*-
from django.contrib import admin
from .integration_credential import IntegrationCredentialAdmin
from .integration_type import IntegrationTypeAdmin
from .. import models

admin.site.register(models.IntegrationType, IntegrationTypeAdmin)
admin.site.register(models.IntegrationCredential, IntegrationCredentialAdmin)
