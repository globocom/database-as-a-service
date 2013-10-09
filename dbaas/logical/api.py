# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceAPI, register
from rest_framework.decorators import link
from .service.product import ProductService
from .service.database import DatabaseService
from .service.credential import CredentialService
from .serializers import ProductSerializer, DatabaseSerializer, CredentialSerializer
from .models import Database
from rest_framework.response import Response
from base.driver.factory import DriverFactory


class ProductAPI(DjangoServiceAPI):
    serializer_class = ProductSerializer
    service_class = ProductService


class DatabaseAPI(DjangoServiceAPI):
    serializer_class = DatabaseSerializer
    service_class = DatabaseService

    @link()
    def status(self, request, pk):
        """ Status of DB """
        try:
            db = Database.objects.get(pk=pk)
            instance = db.instance
            DriverFactory.factory(instance)
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
    serializer_class = CredentialSerializer
    service_class = CredentialService


register('product', ProductAPI)
register('database', DatabaseAPI)
register('credential', CredentialAPI)

