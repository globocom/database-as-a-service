# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin as django_admin
from django.utils.translation import ugettext_lazy as _
from django_services import admin
from ..service.databaseinfra import DatabaseInfraService
from ..models import Instance
from ..forms import DatabaseInfraForm, InstanceModelFormSet
from dbaas_cloudstack.models import DatabaseInfraAttr


from util.html import render_progress_bar


class DatabaseInfraAttrInline(django_admin.TabularInline):
    model = DatabaseInfraAttr
    max_num = 2
    fields = ('ip', 'dns', 'is_write',)
    template = 'admin/physical/shared/inline_form.html'
    def has_delete_permission(self, request, obj=None):
        return False

class InstanceAdmin(django_admin.TabularInline):
    model = Instance
    fields = ('hostname', 'dns', 'address', 'port', 'is_active', 'is_arbiter')
    # max_num = 1
    # can_delete = False
    extra = 1
    formset = InstanceModelFormSet


class DatabaseInfraAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseInfraService
    search_fields = ("name", "user", "instances__address",)
    list_display = ("name", "user", "environment", "show_instances", "capacity_bar")
    list_filter = ("engine", "environment")
    save_on_top = True
    
    add_form_template = "admin/physical/databaseinfra/add_form.html"
    change_form_template = "admin/physical/databaseinfra/change_form.html"
    
    inlines = [
        InstanceAdmin,
        DatabaseInfraAttrInline,
    ]

    def capacity_bar(self, datainfra):
        return render_progress_bar(datainfra.used, datainfra.capacity)
    capacity_bar.short_description = "Capacity"
    capacity_bar.admin_order_field = 'capacity'

    def show_instances(self, datainfra):
        html_instances = []
        for instance in datainfra.instances.all():
            if not instance.is_active:
                html_instances.append("<span style='color: #CCC'>%s</span>" % unicode(instance))
            else:
                if instance.is_arbiter:
                    html_instances.append("%s (arbiter)" % unicode(instance))
                else:
                    html_instances.append(unicode(instance))
        return "<br/>".join(html_instances)

    show_instances.allow_tags = True
    show_instances.short_description = "Instances"

   # def add_view(self, request, form_url='', extra_context=None):
   #     self.form = DatabaseInfraForm
   #     return super(DatabaseInfraAdmin, self).add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.form = DatabaseInfraForm
        return super(DatabaseInfraAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)
