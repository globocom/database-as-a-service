from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from logical.models import Database
from dbaas.middleware import UserMiddleware
from account.models import AccountUser, Team
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from utils import (get_url_env, get_database, log_and_response)


class ServiceRemove(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def put(self, request, database_name, format=None):
        data = request.DATA
        if not data:
            return Response("Invalid request", status=400)

        user = data.get('user')
        team = data.get('team')
        # data.get('plan')
        env = get_url_env(request)

        UserMiddleware.set_current_user(request.user)
        env = get_url_env(request)
        try:
            database = get_database(database_name, env)
        except IndexError as e:
            msg = "Database id provided does not exist {} in {}.".format(
                database_name, env)
            return log_and_response(
                msg=msg, e=e, http_status=status.HTTP_404_NOT_FOUND
            )

        try:
            dbaas_user = AccountUser.objects.get(email=user)
        except ObjectDoesNotExist as e:
            msg = "User does not exist."
            return log_and_response(
                msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except MultipleObjectsReturned as e:
            msg = "There are multiple user for {} email.".format(user)
            return log_and_response(
                msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            dbaas_team = Team.objects.get(name=team)
        except ObjectDoesNotExist as e:
            msg = "Team does not exist."
            return log_and_response(
                msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            dbaas_user.team_set.get(name=dbaas_team.name)
        except ObjectDoesNotExist as e:
            msg = "The user is not on {} team.".format(dbaas_team.name)
            return log_and_response(
                msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        database.team = dbaas_team
        database.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, database_name, format=None):
        UserMiddleware.set_current_user(request.user)
        env = get_url_env(request)
        try:
            database = get_database(database_name, env)
        except IndexError as e:
            msg = "Database id provided does not exist {} in {}.".format(
                database_name, env)
            return log_and_response(
                msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        database.delete()
        return Response(status.HTTP_204_NO_CONTENT)
