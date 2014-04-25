# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from rest_framework import viewsets, serializers
from account import models
import logging

LOG = logging.getLogger(__name__)

class TeamSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Team
        fields = ('url', 'id', 'name',)


class TeamAPI(viewsets.ReadOnlyModelViewSet):
    """
    Environment API
    """
    serializer_class = TeamSerializer
    queryset = models.Team.objects.all()

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = models.Team.objects.all()
        username = self.request.QUERY_PARAMS.get('username', None)
        try:
            if username is not None:
                LOG.info("filtering teams by username %s" % username)
                user = models.AccountUser.objects.get(username=username)
                queryset = queryset.filter(users__username=username)
        except:
            LOG.warning("username %s not found. Returning an empty list of teams." % username)
            queryset = models.Team.objects.none()
    
        return queryset

