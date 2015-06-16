# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.project import ProjectService
from ..forms import ProjectForm


class ProjectAdmin(admin.DjangoServicesAdmin):
    form = ProjectForm
    service_class = ProjectService
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "is_active",)
