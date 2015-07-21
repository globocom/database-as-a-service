# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from account import models


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.AccountUser
        fields = ('url', 'id', 'username', 'email', 'is_active',)


class UserAPI(viewsets.ReadOnlyModelViewSet):

    """
    Environment API
    """
    serializer_class = UserSerializer
    queryset = models.AccountUser.objects.all()
