# encoding: utf-8
from django.contrib import admin

from base.models import Host

class HostAdmin(admin.ModelAdmin):
    search_fields = ["fqdn"]
    list_filter = ("is_active", )
    save_on_top = True
