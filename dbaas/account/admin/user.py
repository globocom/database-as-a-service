# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.contrib.auth.admin import UserAdmin

LOG = logging.getLogger(__name__)


class UserAdmin(UserAdmin):

    fieldsets_basic = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        else:
            if request.user.is_superuser:
                return super(UserAdmin, self).get_fieldsets(request, obj=obj)
            else:
                return self.fieldsets_basic
