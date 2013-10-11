# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceSerializer
from . import models


class ProductSerializer(DjangoServiceSerializer):

    class Meta:
        model = models.Product


class DatabaseSerializer(DjangoServiceSerializer):

    class Meta:
        model = models.Database


class CredentialSerializer(DjangoServiceSerializer):

    class Meta:
        model = models.Credential

class BindSerializer(DjangoServiceSerializer):

    class Meta:
        model = models.Bind
