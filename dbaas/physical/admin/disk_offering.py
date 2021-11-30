# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from ..forms.disk_offerring import DiskOfferingForm


class DiskOfferingAdmin(admin.ModelAdmin):
    form = DiskOfferingForm
    search_fields = ("name",)
    list_display = ("name", "size_gb", "selected_environments")
    save_on_top = True
    filter_horizontal = ("environments",)

    def save_model(self, request, obj, form, change):
        obj.size_kb = obj.converter_gb_to_kb(form.cleaned_data['size_gb'])
        obj.save()

    def selected_environments(self, obj):
        return ",".join(obj.environments.values_list('name', flat=True))
