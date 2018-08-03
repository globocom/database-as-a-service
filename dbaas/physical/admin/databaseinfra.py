# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin as django_admin
from django.utils.translation import ugettext_lazy as _
from django_services import admin
from ..service.databaseinfra import DatabaseInfraService
from ..models import Instance
from ..forms import DatabaseInfraForm, InstanceModelFormSet


from util.html import render_progress_bar


class InstanceAdmin(django_admin.TabularInline):
    model = Instance
    fields = ('hostname', 'dns', 'address', 'port',
              'instance_type', 'shard', 'is_active', 'read_only',)
    # max_num = 1
    # can_delete = False
    extra = 1
    template = 'admin/physical/shared/inline_form.html'
    formset = InstanceModelFormSet


class DatabaseInfraAdmin(admin.DjangoServicesAdmin):
    search_fields = (
        "name", "user", "instances__address", "instances__dns",
        "instances__hostname__hostname"
    )
    service_class = DatabaseInfraService
    list_display = (
        "name", "user", "environment", "show_instances"
    )
    list_filter = ("engine", "environment")
    save_on_top = True

    add_form_template = "admin/physical/databaseinfra/add_form.html"
    change_form_template = "admin/physical/databaseinfra/change_form.html"

    inlines = [
        InstanceAdmin,
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.plan and not obj.plan.is_pre_provisioned:
                return self.readonly_fields + ('disk_offering', )
        return self.readonly_fields

    def show_instances(self, datainfra):
        html_instances = []
        for instance in datainfra.instances.all():
            if not instance.is_active:
                html_instances.append(
                    "<span style='color: #CCC'>%s</span>" % unicode(instance))
            else:
                if instance.instance_type == instance.MONGODB_ARBITER:
                    html_instances.append("%s (arbiter)" % unicode(instance))
                else:
                    html_instances.append(unicode(instance))
        return "<br/>".join(html_instances)

    show_instances.allow_tags = True
    show_instances.short_description = "Instances"

   # def add_view(self, request, form_url='', extra_context=None):
   #     self.form = DatabaseInfraForm
   # return super(DatabaseInfraAdmin, self).add_view(request, form_url,
   # extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.form = DatabaseInfraForm
        return super(DatabaseInfraAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)
