from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from ..views import dashboard
# 
admin.site.register_view('/dashboard/', view=dashboard)

