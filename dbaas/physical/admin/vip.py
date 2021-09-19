# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin


class VipAdmin(admin.ModelAdmin):
    search_fields = ("identifier", "infra")
    list_display = ("identifier", "infra", "vip_ip", "original_vip")
    search_fields = ('infra__name',)
    list_filter = ('infra',)
    #save_on_top = True 
