# -*- coding:utf-8 -*-
from django.contrib import admin
from .. import models

admin.site.register(models.IntegrationType, )
admin.site.register(models.IntegrationCredential, )
