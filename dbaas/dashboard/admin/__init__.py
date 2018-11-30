# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from ..views import dashboard, sofia_dashboard

import admin
admin.site.register_view('/dashboard/', view=dashboard)
admin.site.register_view('/dashboard/sofia_dashboard/',
                         name='Sofia Dashboard',
                         view=sofia_dashboard)
