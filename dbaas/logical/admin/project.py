# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.project import ProjectService


class ProjectAdmin(admin.DjangoServicesAdmin):
    service_class = ProjectService
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "is_active", "slug")
