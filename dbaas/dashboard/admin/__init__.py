# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from ..views import dashboard

import admin
admin.site.register_view('/dashboard/', view=dashboard)
