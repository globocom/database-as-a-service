from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from adminplus.sites import AdminSitePlus
from ..views import dashboard

#hack to pass test
if not isinstance(admin.site, AdminSitePlus):
    admin.site = AdminSitePlus()

admin.site.register_view('/dashboard/', view=dashboard)

