from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from rest_framework import status
from logical.models import Database
from notification.models import TaskHistory
from ..utils import get_url_env, get_database, LOG
from django.db.models import Q


class GetServiceStatus(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def get(self, request, database_name, format=None):
        env = get_url_env(request)
        LOG.info("Database name {}. Environment {}".format(
            database_name, env)
        )
        try:
            database = get_database(database_name, env)
            database_status = database.status
        except IndexError as e:
            database_status = 0
            LOG.warn(
                "There is not a database with this {} name on {}. {}".format(
                    database_name, env, e
                )
            )

        LOG.info("Status = {}".format(database_status))
        task = TaskHistory.objects.filter(
            Q(arguments__contains=database_name) &
            Q(arguments__contains=env), task_status="RUNNING"
        ).order_by("created_at")

        LOG.info("Task {}".format(task))

        if database_status == Database.ALIVE:
            database_status = status.HTTP_204_NO_CONTENT
        elif database_status == Database.DEAD and not task:
            database_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            database_status = status.HTTP_202_ACCEPTED

        return Response(status=database_status)