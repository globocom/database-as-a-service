# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
from django.shortcuts import get_object_or_404
from django.views.generic.detail import BaseDetailView
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from .models import ExtraDns
from logical.models import Database


class ExtraDnsView(BaseDetailView):
    model = ExtraDns

    def check_permission(self, request, perm, obj):
        if not request.user.has_perm(perm, obj=obj):
            raise PermissionDenied

    def as_json(self, obj):
        if isinstance(obj, ExtraDns):
            obj = {"extradns": {"dns": obj.dns, "pk": obj.pk}}
        output = json.dumps(obj, indent=4)
        return HttpResponse(output, content_type="application/json")

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        dns = request.POST.get("dns", None)
        database_id = request.POST.get("database_id", None)
        database = get_object_or_404(Database, pk=database_id)

        # check permission
        self.check_permission(request, "extra_dns.add_extradns", database)
        try:
            extradns = ExtraDns(dns=dns, database=database)
            extradns.save()
            return self.as_json(extradns)

        except Exception, e:
            return self.as_json({"error": ", ".join(e.messages)})

    @method_decorator(csrf_exempt)
    def delete(self, request, *args, **kwargs):
        extra_dns = self.get_object()

        # check permission
        self.check_permission(request, "extra_dns.delete_extradns", extra_dns)

        extra_dns.delete()
        return self.as_json(extra_dns)
