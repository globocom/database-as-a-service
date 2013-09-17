# encoding: utf-8
from django.contrib import admin

from base.models import Environment

class EnvironmentAdmin(admin.ModelAdmin):
    search_fields = ("name", )
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    save_on_top = True