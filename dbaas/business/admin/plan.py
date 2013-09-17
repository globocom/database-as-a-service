# encoding: utf-8
from django.contrib import admin

from business.models import PlanAttribute


class PlanAttributeInline(admin.TabularInline):
    model = PlanAttribute


class PlanAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    save_on_top = True
    inlines = [
        PlanAttributeInline,
    ]

