# -*- coding: utf-8 -*-
from listPlans import ListPlans
from getServiceStatus import GetServiceStatus
from getServiceInfo import GetServiceInfo
from serviceAdd import ServiceAdd
from serviceRemove import ServiceRemove

import re
import logging

import requests
from slugify import slugify
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from networkapiclient import Ip, Network
from django.utils.functional import cached_property

from util import get_credentials_for
from util.decorators import REDIS_CLIENT
from util import simple_health_check
from physical.models import Plan, Environment, PlanNotFound, Pool
from account.models import AccountUser, Team
from notification.models import TaskHistory
from notification.tasks import TaskRegister
from workflow.steps.util.base import ACLFromHellClient
from maintenance.models import DatabaseCreate
from dbaas_credentials.models import CredentialType
from logical.validators import database_name_evironment_constraint
from logical.models import Database
from logical.forms import DatabaseForm
from dbaas.middleware import UserMiddleware
from utils import get_plans_dict, get_url_env





class ServiceAppBind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def add_acl_for_hosts(self, database, app_name):

        infra = database.infra
        hosts = infra.hosts

        acl_from_hell_client = ACLFromHellClient(database.environment)
        for host in hosts:

            resp = acl_from_hell_client.add_acl(
                database,
                app_name,
                host.hostname
            )
            if not resp.ok:
                msg = "Error for {} on {}.".format(
                    database.name, database.environment.name
                )
                return log_and_response(
                    msg=msg, e=resp.content,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        acl_from_hell_client.add_acl_for_vip_if_needed(database, app_name)

        return None

    @staticmethod
    def _handle_app_name(app_name):
        return app_name[0] if isinstance(app_name, list) else app_name

    def post(self, request, database_name, format=None):
        """This method binds a App to a database through tsuru."""
        env = get_url_env(request)
        data = request.DATA
        LOG.debug("Tsuru Bind App POST Request DATA {}".format(data))

        response = check_database_status(database_name, env)
        if not isinstance(response, self.model):
            return response

        database = response
        self.add_acl_for_hosts(
            database,
            self._handle_app_name(data['app-name'])
        )

        hosts, ports = database.infra.get_driver().get_dns_port()
        ports = str(ports)
        if database.databaseinfra.engine.name == 'redis':
            redis_password = database.databaseinfra.password
            endpoint = database.get_endpoint_dns().replace(
                '<password>', redis_password
            )

            env_vars = {
                "DBAAS_REDIS_PASSWORD": redis_password,
                "DBAAS_REDIS_ENDPOINT": endpoint,
                "DBAAS_REDIS_HOST": hosts,
                "DBAAS_REDIS_PORT": ports
            }

            if 'redis_sentinel' in database.infra.get_driver().topology_name():
                env_vars = {
                    "DBAAS_SENTINEL_PASSWORD": redis_password,
                    "DBAAS_SENTINEL_ENDPOINT": endpoint,
                    "DBAAS_SENTINEL_ENDPOINT_SIMPLE": database.get_endpoint_dns_simple(),  # noqa
                    "DBAAS_SENTINEL_SERVICE_NAME": database.databaseinfra.name,
                    "DBAAS_SENTINEL_HOSTS": hosts,
                    "DBAAS_SENTINEL_PORT": ports
                }

        else:
            try:
                credential = (
                    database.credentials.filter(privileges='Owner')
                    or database.credentials.all()
                )[0]
            except IndexError as e:
                msg = ("Database {} in env {} does not have "
                       "credentials.").format(
                    database_name, env
                )

                return log_and_response(
                    msg=msg, e=e,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            endpoint = database.get_endpoint_dns().replace(
                '<user>:<password>', "{}:{}".format(
                    credential.user, credential.password
                )
            )

            kind = ''
            if endpoint.startswith('mysql'):
                kind = 'MYSQL_'
            if endpoint.startswith('mongodb'):
                kind = 'MONGODB_'

            env_vars = {
                "DBAAS_{}USER".format(kind): credential.user,
                "DBAAS_{}PASSWORD".format(kind): credential.password,
                "DBAAS_{}ENDPOINT".format(kind): endpoint,
                "DBAAS_{}HOSTS".format(kind): hosts,
                "DBAAS_{}PORT".format(kind): ports
            }

        return Response(env_vars, status.HTTP_201_CREATED)

    def delete(self, request, database_name, format=None):
        """This method unbinds a App to a database through tsuru."""
        env = get_url_env(request)
        data = request.DATA
        LOG.debug("Tsuru Unbind App DELETE Request DATA {}".format(data))

        response = check_database_status(database_name, env)
        if not isinstance(response, Database):
            return response

        database = response

        acl_from_hell_client = ACLFromHellClient(database.environment)
        acl_from_hell_client.remove_acl(
            database,
            self._handle_app_name(data['app-name'])
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceUnitBind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def post(self, request, database_name, format=None):
        return Response(None, status.HTTP_201_CREATED)

    def delete(self, request, database_name, format=None):
        return Response(status.HTTP_204_NO_CONTENT)






def last_database_create(database_name, env):
    """This function returns the most recent DatabaseCreate's task.

    Parameters:
    database_name (str): Name of the database
    env (str): It represents the database environment (prod or dev)

    Returns:
    DatabaseCreate: DatabaseCreate object
    """
    return DatabaseCreate.objects.filter(
        name=database_name,
        environment__name=env
    ).last()


def check_database_status(database_name, env):
    """This function looks for a DatabaseCreate task and returns a http
    response or the Database itself depeding on the context. If the
    DatabaseCreate task is still running of failed, a http response is
    returned, otherwise this functions tries to retrieve the Database with
    the get_database function.

    Parameters:
    database_name (str): Name of the database
    env (str): It represents the database environment (prod or dev)

    Returns:
    Database or Response: Database or Rest Framework Response object
    """
    database_create = last_database_create(database_name, env)

    LOG.info(
        "Task {}".format(getattr(database_create, 'task', 'No tasks found'))
    )

    if database_create:
        if database_create.is_running:
            msg = "Database {} in env {} is beeing created.".format(
                database_name, env)
            return log_and_response(
                msg=msg, http_status=status.HTTP_412_PRECONDITION_FAILED)

        elif database_create.is_status_error:
            msg = ("A error ocurred creating database {} in env {}. Check "
                   "error on task history in https://dbaas.globoi.com").format(
                database_name, env)
            return log_and_response(
                msg=msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        database = get_database(database_name, env)
    except IndexError as e:
        msg = "Database {} does not exist in env {}.".format(
            database_name, env)
        return log_and_response(
            msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except MultipleObjectsReturned as e:
        msg = "There are multiple databases called {} in {}.".format(
            database_name, env)
        return log_and_response(
            msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        msg = "Something ocurred on dbaas, please get in touch with your DBA."
        return log_and_response(
            msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not(database and database.status):
        msg = "Database {} is not Alive.".format(database_name)
        return log_and_response(
            msg=msg, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return database