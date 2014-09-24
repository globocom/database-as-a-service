from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
import logging
from logical.models import Database
from physical.models import Plan, Environment
from account.models import AccountUser, Team
from rest_framework import status
from slugify import slugify
from notification.tasks import create_database
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from notification.models import TaskHistory

LOG = logging.getLogger(__name__)

class ListPlans(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Plan

    def get(self, request, format=None):
        """
        Return a list of all plans.
        """
        env = get_url_env(request)

        hard_plans = Plan.objects.filter(environments__name=env).values('name', 'description'
            , 'environments__name').extra(where=['is_active=True', 'provider={}'.format(Plan.CLOUDSTACK)])

        plans = get_plans_dict(hard_plans)

        return Response(plans)

class GetServiceStatus(APIView):
    """
    Return the database status
    """
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def get(self, request, database_name, format=None):
        env = get_url_env(request)
        LOG.info("Database name {}. Environment {}".format(database_name, env))
        try:
            database_status = Database.objects.filter(name= database_name, environment__name=env).values_list('status', flat=True)[0]
        except IndexError, e:
            database_status=0
            LOG.warn("There is not a database with this {} name on {}. {}".format(database_name, env,e))

        LOG.info("Status = {}".format(database_status))
        task = TaskHistory.objects.filter(Q(arguments__contains=database_name) &
                Q(arguments__contains=env), task_status="RUNNING",).order_by("created_at")

        LOG.info("Task {}".format(task))

        if database_status == Database.ALIVE:
            database_status = status.HTTP_204_NO_CONTENT
        elif database_status == Database.DEAD and not task:
            database_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            database_status = status.HTTP_202_ACCEPTED

        return Response(status=database_status)


class GetServiceInfo(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def get(self, request, database_name, format=None):
        env = get_url_env(request)
        try:
            info = Database.objects.filter(name= database_name, environment__name=env).values('used_size_in_bytes', )[0]
            info['used_size_in_bytes'] = str(info['used_size_in_bytes'])
        except IndexError, e:
            info = {}
            LOG.warn("There is not a database {} on {}. {}".format(database_name, env,e))

        LOG.info("Info = {}".format(info))

        return Response(info)


class ServiceBind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def post(self, request, database_name, format=None):
        env = get_url_env(request)
        data = request.DATA
        LOG.debug("Request DATA {}".format(data))

        try:
            database = Database.objects.get(name=database_name, environment__name=env)
        except ObjectDoesNotExist, e:
            msg = "Database {} does not exist in env {}.".format(database_name, env)
            return log_and_response(msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        task = TaskHistory.objects.filter(Q(arguments__contains=database_name) &
            Q(arguments__contains=env), task_status="RUNNING",).order_by("created_at")

        LOG.info("Task {}".format(task))
        if task:
            msg = "Database {} in env {} is beeing created.".format(database_name, env)
            return log_and_response(msg=msg, http_status=status.HTTP_412_PRECONDITION_FAILED)

        if not(database and database.status):
            msg = "Database {} is not Alive.".format(database_name)
            return log_and_response(msg=msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            credential = database.credentials.all()[0]
        except IndexError, e:
            msg = "Database {} in env {} does not have credentials.".format(database_name, env)
            return log_and_response(msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        endpoint = database.endpoint.replace('<user>:<password>',"{}:{}".format(
            credential.user, credential.password))

        return Response({"user":credential.user, "password": credential.password, "endpoint": endpoint},
            status.HTTP_201_CREATED)

    def delete(self, request, database_name, format=None):
        env = get_url_env(request)
        try:
            database = Database.objects.get(name=database_name, environment__name=env)
        except ObjectDoesNotExist, e:
            msg = "Database id provided does not exist {} in {}.".format(database_name, env)
            return log_and_response(msg=msg, e=e,http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not database.is_in_quarantine:
            database.delete()

        return Response(status.HTTP_204_NO_CONTENT)



class ServiceUnbind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def delete(self, request, database_name, unbind_ip, format=None):
        return Response(status.HTTP_204_NO_CONTENT)


class ServiceAdd(APIView):

    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def post(self, request, format=None):
        data = request.DATA
        name = data['name']
        user = data['user']
        team = data['team']
        env = get_url_env(request)

        try:
            Database.objects.get(name=name, environment__name=env)
            msg = "There is already a database called {} in {}.".format(name, env)
            return log_and_response(msg=msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist, e:
            pass

        try:
            dbaas_user =  AccountUser.objects.get(email=user)
        except ObjectDoesNotExist, e:
            msg = "User does not exist"
            return log_and_response(msg=msg, e=e,http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            dbaas_team = Team.objects.get(name=team)
        except ObjectDoesNotExist, e:
            msg = "Team does not exist."
            return log_and_response(msg=msg, e=e,http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            dbaas_user.team_set.get(name=dbaas_team.name)
        except ObjectDoesNotExist, e:
            msg = "The user is not on {} team".format(dbaas_team.name)
            return log_and_response(msg=msg, e=e,http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not 'plan' in data:
            msg = "Plan was not found"
            return log_and_response(msg=msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        plan = data['plan']

        hard_plans = Plan.objects.values('name', 'description', 'pk'
            , 'environments__name').extra(where=['is_active=True', 'provider={}'.format(Plan.CLOUDSTACK)])

        plans = get_plans_dict(hard_plans)
        plan = [splan for splan in plans if splan['name']==plan]
        LOG.info("Plan: {}".format(plan))

        if any(plan):
            dbaas_plan = Plan.objects.get(pk=plan[0]['pk'])
        else:
            msg = "Plan was not found"
            return log_and_response(msg=msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            dbaas_environment = Environment.objects.get(name= env)
        except(ObjectDoesNotExist,IndexError), e:
            msg = "Environment does not exist."
            return log_and_response(msg=msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        create_database.delay(name, dbaas_plan, dbaas_environment,dbaas_team,
                                        None, 'Database from Tsuru', dbaas_user)

        return Response(status=status.HTTP_201_CREATED,)


def get_plans_dict(hard_plans):
    plans = []
    for hard_plan in hard_plans:
        hard_plan['description'] = hard_plan['name'] +'-'+ hard_plan['environments__name']
        hard_plan['name'] = slugify(hard_plan['description'])
        del hard_plan['environments__name']
        plans.append(hard_plan)

    return plans

def get_url_env(request):
    return request._request.path.split('/')[1]

def log_and_response(msg, http_status, e="Conditional Error."):
    LOG.warn(msg)
    LOG.warn("Error: {}".format(e))

    return Response(msg, http_status)
