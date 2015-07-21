# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from logical import models


class ProjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Project
        fields = ('url', 'id', 'name',)


class ProjectAPI(viewsets.ModelViewSet):

    """
    Project API
    """
    serializer_class = ProjectSerializer
    queryset = models.Project.objects.all()
