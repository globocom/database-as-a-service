# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.shortcuts import get_object_or_404
from django.views.generic.detail import BaseDetailView
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from .models import Credential, Database
from util import as_json


class CredentialView(BaseDetailView):
    model = Credential

    @method_decorator(csrf_exempt(as_json))
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", None)
        database_id = request.POST.get("database_id", None)
        try:
            database = get_object_or_404(Database, pk=database_id)
            credential = Credential.create_new_credential(username, database)
            return {"credential" : { "user": credential.user, "password": credential.password, "id": credential.pk } }
        except ValidationError, e:
            return { "error": ", ".join(e.messages) }

    @method_decorator(csrf_exempt(as_json))
    def put(self, request, *args, **kwargs):
        credential = self.get_object()
        credential.reset_password()
        return {'password': credential.password }

    @method_decorator(csrf_exempt(as_json))
    def delete(self, request, *args, **kwargs):
        credential = self.get_object()
        credential.delete()
        return {'password': credential.password }
