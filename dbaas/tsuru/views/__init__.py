# -*- coding: utf-8 -*-
from listPlans import ListPlans
from getServiceStatus import GetServiceStatus
from getServiceInfo import GetServiceInfo
from serviceAdd import ServiceAdd

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


DATABASE_NAME_REGEX = re.compile('^[a-z][a-z0-9_]+$')


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


class ServiceRemove(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def put(self, request, database_name, format=None):
        data = request.DATA
        user = data['user']
        team = data['team']
        data['plan']
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


def get_network_from_ip(ip, database_environment):
    net_api_credentials = get_credentials_for(
        environment=database_environment,
        credential_type=CredentialType.NETWORKAPI
    )

    ip_client = Ip.Ip(
        net_api_credentials.endpoint, net_api_credentials.user,
        net_api_credentials.password
    )

    ips = ip_client.get_ipv4_or_ipv6(ip)
    ips = ips['ips']
    if type(ips) != list:
        ips = [ips]

    net_ip = ips[0]
    network_client = Network.Network(
        net_api_credentials.endpoint, net_api_credentials.user,
        net_api_credentials.password
    )

    network = network_client.get_network_ipv4(net_ip['networkipv4'])
    network = network['network']

    return '{}.{}.{}.{}/{}'.format(
        network['oct1'], network['oct2'], network['oct3'],
        network['oct4'], network['block']
    )


def check_acl_service_and_get_unit_network(database, data,
                                           ignore_ip_error=False):

    try:
        acl_credential = get_credentials_for(
            environment=database.environment,
            credential_type=CredentialType.ACLAPI
        )
    except IndexError:
        error = 'The {} do not have integration with ACLAPI'.format(
            database.environment
        )
        return log_and_response(
            msg=None, e=error, http_status=status.HTTP_201_CREATED
        )

    health_check_info = acl_credential.get_parameters_by_group('hc')
    try:
        health_check_url = (acl_credential.endpoint
                            + health_check_info['health_check_url'])
        simple_hc = simple_health_check.SimpleHealthCheck(
            health_check_url=health_check_url,
            service_key=health_check_info['key_name'],
            redis_client=REDIS_CLIENT, http_client=requests,
            http_request_exceptions=(Exception,), verify_ssl=False,
            health_check_request_timeout=int(health_check_info['timeout'])
        )
    except KeyError as e:
        msg = "AclApi Credential configured improperly."
        return log_and_response(
            msg=msg, e=e,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    try:
        simple_hc.check_service()
    except simple_health_check.HealthCheckError as e:
        LOG.warn(e)
        msg = ("We are experiencing errors with the acl api, please try again "
               "later.")
        return log_and_response(
            msg=msg, e=e,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        LOG.warn(e)

    try:
        return get_network_from_ip(
            data.get('unit-host'), database.environment
        )
    except Exception as e:
        LOG.warn(e)
        msg = ("We are experiencing errors with the network api, please try "
               "get network again later")
        if not ignore_ip_error:
            return log_and_response(
                msg=msg, e=e,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
