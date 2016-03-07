# -*- coding: utf-8 -*-
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
from dbaas_aclapi.tasks import bind_address_on_database
from dbaas_aclapi.tasks import unbind_address_on_database
from dbaas_aclapi.models import DatabaseBind
from dbaas_aclapi.models import DESTROYING, CREATED, CREATING
from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from django.db import IntegrityError
import re

LOG = logging.getLogger(__name__)


class ListPlans(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Plan

    def get(self, request, format=None):
        """
        Return a list of all plans.
        """
        env = get_url_env(request)

        hard_plans = Plan.objects.filter(environments__name=env).values('name', 'description',
                                                                        'environments__name').extra(where=['is_active=True', 'provider={}'.format(Plan.CLOUDSTACK)])

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
            database_status = Database.objects.filter(name=database_name,
                                                      environment__name=env).values_list('status', flat=True)[0]
        except IndexError as e:
            database_status = 0
            LOG.warn("There is not a database with this {} name on {}. {}".format(
                database_name, env, e))

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
            info = Database.objects.filter(
                name=database_name, environment__name=env).values('used_size_in_bytes', )[0]
            info['used_size_in_bytes'] = str(info['used_size_in_bytes'])
        except IndexError as e:
            info = {}
            LOG.warn(
                "There is not a database {} on {}. {}".format(database_name, env, e))

        LOG.info("Info = {}".format(info))

        return Response(info)


class ServiceAppBind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def post(self, request, database_name, format=None):
        env = get_url_env(request)
        data = request.DATA
        LOG.debug("Request DATA {}".format(data))

        response = check_database_status(database_name, env)
        if type(response) != Database:
            return response

        database = response

        if database.databaseinfra.engine.name == 'redis':
            redis_password = database.databaseinfra.password
            endpoint = database.get_endpoint_dns().replace(
                '<password>', redis_password)

            env_vars = {"DBAAS_REDIS_PASSWORD": redis_password,
                        "DBAAS_REDIS_ENDPOINT": endpoint
                        }

            if database.plan.is_ha:
                env_vars = {"DBAAS_SENTINEL_PASSWORD": redis_password,
                            "DBAAS_SENTINEL_ENDPOINT": endpoint,
                            "DBAAS_SENTINEL_SERVICE_NAME": database.databaseinfra.name
                            }

        else:
            try:
                credential = database.credentials.all()[0]
            except IndexError as e:
                msg = "Database {} in env {} does not have credentials.".format(
                    database_name, env)
                return log_and_response(msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            endpoint = database.endpoint.replace('<user>:<password>', "{}:{}".format(
                credential.user, credential.password))

            kind = ''
            if endpoint.startswith('mysql'):
                kind = 'MYSQL_'
            if endpoint.startswith('mongodb'):
                kind = 'MONGODB_'

            env_vars = {
                "DBAAS_{}USER".format(kind): credential.user,
                "DBAAS_{}PASSWORD".format(kind): credential.password,
                "DBAAS_{}ENDPOINT".format(kind): endpoint
            }

        return Response(env_vars, status.HTTP_201_CREATED)

    def delete(self, request, database_name, format=None):
        env = get_url_env(request)
        data = request.DATA
        LOG.debug("Request DATA {}".format(data))

        response = check_database_status(database_name, env)
        if type(response) != Database:
            return response

        return Response(status.HTTP_204_NO_CONTENT)


class ServiceUnitBind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def post(self, request, database_name, format=None):
        env = get_url_env(request)

        response = check_database_status(database_name, env)
        if type(response) != Database:
            return response

        database = response
        data = request.DATA
        LOG.debug("Request DATA {}".format(data))
        unit_host = data.get('unit-host') + '/32'
        created = False

        transaction.set_autocommit(False)
        database_bind = DatabaseBind(database=database, bind_address=unit_host,
                                     binds_requested=1)

        try:
            database_bind.save()
            created = True
        except IntegrityError as e:
            LOG.info("IntegrityError: {}".format(e))

            try:
                db_bind = DatabaseBind.objects.get(database=database,
                                                   bind_address=unit_host)

                bind = DatabaseBind.objects.select_for_update().filter(
                    id=db_bind.id)[0]
                if bind.bind_status in [CREATED, CREATING]:
                    bind.binds_requested += 1
                    bind.save()
                else:
                    raise Exception("Binds are beeing destroyed!")
            except (IndexError, ObjectDoesNotExist) as e:
                LOG.debug("DatabaseBind is under destruction! {}".format(e))
                msg = "We are destroying your binds to {}. Please wait.".format(database_name)
                return log_and_response(msg=msg, e=e,
                                        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            LOG.debug("Finishing transaction!")
            transaction.commit()
            transaction.set_autocommit(True)

        if created:
            bind_address_on_database.delay(database_bind=database_bind,
                                           user=request.user)

        return Response(None, status.HTTP_201_CREATED)

    def delete(self, request, database_name, format=None):
        env = get_url_env(request)
        data = request.DATA
        LOG.debug("Request DATA {}".format(data))

        response = check_database_status(database_name, env)
        if type(response) != Database:
            return response

        database = response
        unbind_ip = data.get('unit-host') + '/32'
        transaction.set_autocommit(False)

        try:
            db_bind = DatabaseBind.objects.get(database=database,
                                               bind_address=unbind_ip)

            database_bind = DatabaseBind.objects.select_for_update().filter(
                id=db_bind.id)[0]

            if database_bind.bind_status != DESTROYING:
                if database_bind.binds_requested > 0:
                    database_bind.binds_requested -= 1

                if database_bind.binds_requested == 0:
                    database_bind.status = DESTROYING

                database_bind.save()
        except (IndexError, ObjectDoesNotExist) as e:
            msg = "DatabaseBind does not exist"
            return log_and_response(msg=msg, e=e,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            LOG.debug("Finishing transaction!")
            transaction.commit()
            transaction.set_autocommit(True)

        if database_bind.binds_requested == 0:
            unbind_address_on_database.delay(database_bind=database_bind,
                                             user=request.user)

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

        name_regexp = re.compile('^[a-z][a-z0-9_]+$')
        if name_regexp.match(name) is None:
            msg = "Your database name must match /^[a-z][a-z0-9_]+$/ ."
            return log_and_response(msg=msg,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            Database.objects.get(name=name, environment__name=env)
            msg = "There is already a database called {} in {}.".format(
                name, env)
            return log_and_response(msg=msg,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ObjectDoesNotExist:
            pass

        try:
            dbaas_user = AccountUser.objects.get(email=user)
        except ObjectDoesNotExist as e:
            msg = "User does not exist."
            return log_and_response(msg=msg, e=e,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            dbaas_team = Team.objects.get(name=team)
        except ObjectDoesNotExist as e:
            msg = "Team does not exist."
            return log_and_response(msg=msg, e=e,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            dbaas_user.team_set.get(name=dbaas_team.name)
        except ObjectDoesNotExist as e:
            msg = "The user is not on {} team.".format(dbaas_team.name)
            return log_and_response(msg=msg, e=e,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            dbaas_environment = Environment.objects.get(name=env)
        except(ObjectDoesNotExist) as e:
            msg = "Environment does not exist."
            return log_and_response(msg=msg,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        databases_used_by_team = dbaas_team.count_databases_in_use(
            environment=dbaas_environment)
        database_alocation_limit = dbaas_team.database_alocation_limit

        if databases_used_by_team >= database_alocation_limit:
            msg = "The database alocation limit of {} has been exceeded for the selected team: {}".format(
                database_alocation_limit, dbaas_team)
            return log_and_response(msg=msg,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if 'plan' not in data:
            msg = "Plan was not found"
            return log_and_response(msg=msg,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        plan = data['plan']
        hard_plans = Plan.objects.values('name', 'description', 'pk',
                                         'environments__name').extra(where=['is_active=True',
                                                                            'provider={}'.format(Plan.CLOUDSTACK)])

        plans = get_plans_dict(hard_plans)
        plan = [splan for splan in plans if splan['name'] == plan]
        LOG.info("Plan: {}".format(plan))

        if any(plan):
            dbaas_plan = Plan.objects.get(pk=plan[0]['pk'])
        else:
            msg = "Plan was not found"
            return log_and_response(msg=msg,
                                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        task_history = TaskHistory()
        task_history.task_name = "create_database"
        task_history.arguments = "Database name: {}".format(name)
        task_history.save()

        create_database.delay(name=name, plan=dbaas_plan,
                              environment=dbaas_environment, team=dbaas_team,
                              project=None, description='Database from Tsuru',
                              task_history=task_history, user=dbaas_user)

        return Response(status=status.HTTP_201_CREATED,)


class ServiceRemove(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def delete(self, request, database_name, format=None):
        env = get_url_env(request)
        try:
            database = Database.objects.filter(
                name=database_name, environment__name=env).exclude(is_in_quarantine=True)[0]
        except IndexError as e:
            msg = "Database id provided does not exist {} in {}.".format(
                database_name, env)
            return log_and_response(msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        database.delete()
        return Response(status.HTTP_204_NO_CONTENT)


def get_plans_dict(hard_plans):
    plans = []
    for hard_plan in hard_plans:
        hard_plan['description'] = hard_plan[
            'name'] + '-' + hard_plan['environments__name']
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


def check_database_status(database_name, env):
    task = TaskHistory.objects.filter(arguments__contains="Database name: {}, Environment: {}".format(
        database_name, env), task_status="RUNNING",)

    LOG.info("Task {}".format(task))
    if task:
        msg = "Database {} in env {} is beeing created.".format(
            database_name, env)
        return log_and_response(msg=msg,
                                http_status=status.HTTP_412_PRECONDITION_FAILED)

    try:
        database = Database.objects.get(
            name=database_name, environment__name=env)
    except ObjectDoesNotExist as e:
        msg = "Database {} does not exist in env {}.".format(
            database_name, env)
        return log_and_response(msg=msg, e=e,
                                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except MultipleObjectsReturned as e:
        msg = "There are multiple databases called {} in {}.".format(
            database_name, env)
        return log_and_response(msg=msg, e=e,
                                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        msg = "Something ocurred on dbaas, please get in touch with your DBA."
        return log_and_response(msg=msg, e=e,
                                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not(database and database.status):
        msg = "Database {} is not Alive.".format(database_name)
        return log_and_response(msg=msg,
                                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return database
