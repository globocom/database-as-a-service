# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from adminplus.sites import AdminSitePlus
from django.contrib.admin import autodiscover

__all__ = ['site', 'autodiscover']

# To ensure AdminSite as admin in tests and on load app (in urls.py),
# all code must access admin.site throught this module.

site = AdminSitePlus()
admin.site = site
