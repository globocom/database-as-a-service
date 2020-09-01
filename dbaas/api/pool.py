# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from rest_framework import viewsets, serializers, status, filters
from rest_framework.response import Response

from logical.models import Database
from physical.models import Environment, Pool
from account.models import Team
from api.team import TeamSerializer


class PoolSerializer(serializers.HyperlinkedModelSerializer):
    teams = TeamSerializer(many=True, read_only=True)

    class Meta:
        model = Database
        fields = (
            'id', 'name', 'environment', 'teams'
        )


class PoolAPI(viewsets.ModelViewSet):

    model = Pool
    serializer_class = PoolSerializer
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        "name",
        "environment",
        "teams__name"
    )

    def create(self, request):
        serializer = self.get_serializer(
            data=request.DATA, files=request.FILES)
        data = serializer.init_data
        env_name = data.get('environment', '')
        if env_name:
            env = Environment.objects.get(name=env_name)
        teams_names = data.pop('teams') if 'teams' in data else []
        teams = Team.objects.filter(name__in=teams_names)
        headers = self.get_success_headers(data)
        data['environment'] = env
        pool = self.model.objects.create(**data)
        for team in teams:
            pool.teams.add(team)
        return Response(
            {"pool": pool.id}, status=status.HTTP_201_CREATED,
            headers=headers
        )

    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     UserMiddleware.set_current_user(request.user)

    #     if instance.is_in_quarantine or instance.is_protected:
    #         return Response(status=status.HTTP_401_UNAUTHORIZED)

    #     instance.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)
