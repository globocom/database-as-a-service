# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.engine import EngineService


class EngineAdmin(admin.DjangoServicesAdmin):
    service_class = EngineService
    search_fields = ("engine_type__name",)
    list_display = ("engine_type", "version", "created_at")
    list_filter = ("engine_type",)
    save_on_top = True
    ordering = ('engine_type__name', )

    def get_queryset(self, request):
        qs = super(EngineAdmin, self).get_queryset(request)
        return qs.order_by('engine_type__name', 'version')
