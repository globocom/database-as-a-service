# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Credential
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
