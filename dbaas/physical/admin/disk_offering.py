# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from ..forms.disk_offerring import DiskOfferingForm


class DiskOfferingAdmin(admin.ModelAdmin):
    form = DiskOfferingForm
    search_fields = ("name",)
    list_display = ("name", "size_gb", "available_size_gb")
    save_on_top = True

    def save_model(self, request, obj, form, change):
        obj.size_kb = obj.converter_gb_to_kb(form.cleaned_data['size_gb'])
        obj.available_size_kb = obj.converter_gb_to_kb(
            form.cleaned_data['available_size_gb']
        )
        obj.save()
