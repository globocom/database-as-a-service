# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin


class VipInstanceGroupAdmin(admin.ModelAdmin):
    search_fields = ("name", "identifier",)
    list_display = ("name", "identifier", "vip", )
    search_fields = ("name", "identifier", "vip__infra__name")
    list_filter = ('vip__infra',)
    #save_on_top = True
