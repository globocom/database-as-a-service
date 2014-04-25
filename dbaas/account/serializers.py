# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services.api import DjangoServiceSerializer
from .models import Team, AccountUser


class TeamSerializer(DjangoServiceSerializer):

    class Meta:
        model = Team


class UserSerializer(DjangoServiceSerializer):

    class Meta:
        model = AccountUser
