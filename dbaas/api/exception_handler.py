# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError


def custom_exception_handler(exc):

    if type(exc) is ValidationError:
        response = Response(status=status.HTTP_400_BAD_REQUEST)
        response.data = { 'error': exc.messages }
    else:
        # Call REST framework's default exception handler first,
        # to get the standard error response.
        response = exception_handler(exc)

    return response
