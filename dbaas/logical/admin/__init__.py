# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from .. import models
from .product import ProductAdmin
from .database import DatabaseAdmin
from .credential import CredentialAdmin
from .bind import BindAdmin

admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Database, DatabaseAdmin)
admin.site.register(models.Credential, CredentialAdmin)
admin.site.register(models.Bind, BindAdmin)
