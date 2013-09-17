# -*- coding:utf-8 -*-
from django.contrib import admin

from business.models import Product, Plan, PlanAttribute

from business.admin.product import ProductAdmin
from business.admin.plan import PlanAdmin

admin.site.register(Product, ProductAdmin)
admin.site.register(Plan, PlanAdmin)
#admin.site.register(PlanAttribute, PlanAttributeAdmin)
