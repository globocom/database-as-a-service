# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin


class IpAdmin(admin.ModelAdmin):
    search_fields = ("identifier", "address")
    list_display = ("identifier", "address", "instance")
    save_on_top = True