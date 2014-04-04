# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceAPI, register
from .service.instance import TeamService, UserService

from .serializers import TeamSerializer, UserSerializer


class TeamAPI(DjangoServiceAPI):
    serializer_class = TeamSerializer
    service_class = TeamService


class UserAPI(DjangoServiceAPI):
    serializer_class = UserSerializer
    service_class = UserService


register('team', TeamAPI)
register('user', UserAPI)
