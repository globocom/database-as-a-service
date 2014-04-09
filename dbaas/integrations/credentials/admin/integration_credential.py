# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin


class IntegrationCredentialAdmin(admin.ModelAdmin):
    search_fields = ("endpoint",)
    list_display = ("endpoint","user",)
    save_on_top = True