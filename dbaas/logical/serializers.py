# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceSerializer
from .models import Product, Database, Credential


class ProductSerializer(DjangoServiceSerializer):

    class Meta:
        model = Product


class DatabaseSerializer(DjangoServiceSerializer):

    class Meta:
        model = Database


class CredentialSerializer(DjangoServiceSerializer):

    class Meta:
        model = Credential


