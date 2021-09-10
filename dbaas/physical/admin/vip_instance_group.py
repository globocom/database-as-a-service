# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin


class VipInstanceGroupAdmin(admin.ModelAdmin):
    search_fields = ("name", "identifier")
    list_display = ("name", "identifier", "vip")
    save_on_top = True
