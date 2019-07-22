# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from django.contrib import admin as django_admin
from ..service.engine import EngineService
from ..models import EnginePatch
from ..forms.engine_patch import engine_patch_formset


class EnginePatchInline(django_admin.StackedInline):
    formset = engine_patch_formset
    model = EnginePatch
    extra = 0

    verbose_name = "Patch Version"


class EngineAdmin(admin.DjangoServicesAdmin):
    service_class = EngineService
    search_fields = ("engine_type__name",)
    readonly_fields = ("version2", "full_inicial_version")
    list_display = ("engine_type", "version", "is_active",
        "version2", "full_inicial_version")
    list_filter = ("engine_type", "is_active")
    save_on_top = True
    ordering = ('engine_type__name', )
    inlines = [EnginePatchInline]

    def get_queryset(self, request):
        qs = super(EngineAdmin, self).get_queryset(request)
        return qs.order_by('engine_type__name', 'version')
