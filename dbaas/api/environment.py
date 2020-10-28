# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from physical.models import Environment


class EnvironmentSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Environment
        fields = ('url', 'id', 'name', 'stage', 'provisioner')


class EnvironmentAPI(viewsets.ReadOnlyModelViewSet):

    """
    Environment API
    """
    model = Environment
    serializer_class = EnvironmentSerializer
    queryset = Environment.objects.all()
    filter_fields = (
        'id',
        'name',
        'stage',
        'provisioner'
    )

    def get_queryset(self):
        params = self.request.GET.dict()
        filter_params = {}
        for k, v in params.iteritems():
            if k == 'get_provisioner_by_label':
                if hasattr(self.model, v.upper()):
                    label_id = getattr(self.model, v.upper())
                    filter_params['provisioner'] = label_id
                else:
                    return self.model.objects.none()
            elif k.split('__')[0] in self.filter_fields:
                filter_params[k] = v
        return self.model.objects.filter(**filter_params)
