# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
from django.shortcuts import get_object_or_404
from django.views.generic.detail import BaseDetailView
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from .models import Credential, Database


class CredentialView(BaseDetailView):
    model = Credential

    def check_permission(self, request, perm, obj):
        if not request.user.has_perm(perm, obj=obj):
            raise PermissionDenied

    def as_json(self, obj):
        if isinstance(obj, Credential):
            obj = {"credential" : { "user": obj.user, "password": obj.password, "pk": obj.pk } }
        output = json.dumps(obj, indent=4)
        return HttpResponse(output, content_type="application/json")


    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", None)
        database_id = request.POST.get("database_id", None)
        try:
            database = get_object_or_404(Database, pk=database_id)

            # check permission
            self.check_permission(request, "logical.add_credential", database)

            credential = Credential.create_new_credential(username, database)
            return self.as_json(credential)
        except ValidationError, e:
            return self.as_json({ "error": ", ".join(e.messages) })

    @method_decorator(csrf_exempt)
    def put(self, request, *args, **kwargs):
        credential = self.get_object()

        # check permission
        self.check_permission(request, "logical.change_credential", credential)

        credential.reset_password()
        return self.as_json(credential)

    @method_decorator(csrf_exempt)
    def delete(self, request, *args, **kwargs):
        credential = self.get_object()

        # check permission
        self.check_permission(request, "logical.delete_credential", credential)

        credential.delete()
        return self.as_json(credential)
