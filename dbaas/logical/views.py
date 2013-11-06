# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import Credential, Database
from util import as_json


# FIXME FIX this to allow csrf with ajax

@csrf_exempt
@as_json
def reset_password(request, credential_id):

    credential = get_object_or_404(Credential, pk=credential_id)
    credential.reset_password()
    return {'password': credential.password }

@csrf_exempt
@as_json
def delete_credential(request, credential_id):

    credential = get_object_or_404(Credential, pk=credential_id)
    credential.delete()
    return {'password': credential.password }

@csrf_exempt
@as_json
def create_credential(request):

    username = request.POST.get("username", None)
    database_id = request.POST.get("database_id", None)
    try:
        database = get_object_or_404(Database, pk=database_id)
        credential = Credential.create_new_credential(username, database)
        return {"credential" : { "user": credential.user, "password": credential.password, "id": credential.pk } }
    except ValidationError, e:
        return { "error": ", ".join(e.messages) }
