# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status, permissions
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


class ObjectPermissions(permissions.DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.change_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.change_%(model_name)s'],
        'HEAD': ['%(app_label)s.change_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

class ObjectPermissionsFilter(object):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    perm_format = '%(app_label)s.change_%(model_name)s'

    def filter_queryset(self, request, queryset, view):
        user = request.user
        model_cls = queryset.model
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.module_name
        }
        permission = self.perm_format % kwargs
        filtered_queryset = model_cls.objects.filter(pk__in=[
            obj.pk for obj in queryset.all() if user.has_perm(permission, obj=obj)
            ])
        return filtered_queryset
