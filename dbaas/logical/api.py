# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceAPI, register
from rest_framework.decorators import link
from .service.product import ProductService
from .service.database import DatabaseService
from .service.credential import CredentialService
from .service.bind import BindService
from . import serializers
from .models import Database
from rest_framework.response import Response
from drivers import factory_for


class ProductAPI(DjangoServiceAPI):
    serializer_class = serializers.ProductSerializer
    service_class = ProductService


class DatabaseAPI(DjangoServiceAPI):
    serializer_class = serializers.DatabaseSerializer
    service_class = DatabaseService

    @link()
    def status(self, request, pk):
        """ Status of DB """
        try:
            db = Database.objects.get(pk=pk)
            instance = db.instance
            factory_for(instance).check_status()
            return Response(
                {'status': 'WORKING'},
                status='200')
        except Database.DoesNotExist:
            return Response(
                {'status': 'Database does not exist.'},
                status='404')
        except Exception as e:
            return Response(
                {'status': 'Error. %s (%s)' % (e.message, type(e))},
                status='400')


class CredentialAPI(DjangoServiceAPI):
    serializer_class = serializers.CredentialSerializer
    service_class = CredentialService


class BindAPI(DjangoServiceAPI):
    serializer_class = serializers.BindSerializer
    service_class = BindService


register('product', ProductAPI)
register('database', DatabaseAPI)
register('credential', CredentialAPI)
register('bind', BindAPI)

