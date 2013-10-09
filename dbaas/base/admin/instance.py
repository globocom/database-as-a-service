# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin as django_admin
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django_services import admin
from ..service.instance import InstanceService
from ..models import Node


class NodeModelFormSet(BaseInlineFormSet):

    def clean(self):
        super(NodeModelFormSet, self).clean()

        for error in self.errors:
            if error:
                return

        completed = 0
        for cleaned_data in self.cleaned_data:
            # form has data and we aren't deleting it.
            if cleaned_data and not cleaned_data.get('DELETE', False):
                completed += 1

        # example custom validation across forms in the formset:
        if completed  == 0:
            raise ValidationError({'nodes': _("Specify at least one valid node")})
        elif completed > 1:
            raise ValidationError({'nodes': _("Currently, you can have only one node per instance")})


class NodeAdmin(django_admin.TabularInline):
    model = Node
    fields = ('address', 'port', 'type', 'is_active',)
    max_num = 1
    can_delete = False
    extra = 1
    formset = NodeModelFormSet


class InstanceAdmin(admin.DjangoServicesAdmin):
    service_class = InstanceService
    search_fields = ("name", "user", "product__name", "nodes__address",)
    list_display = ("name", "user", "node", "product")
    list_filter = ("product", "engine", "plan")
    save_on_top = True

    inlines = [
        NodeAdmin
    ]

