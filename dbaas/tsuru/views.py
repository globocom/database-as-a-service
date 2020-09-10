# -*- coding: utf-8 -*-
import re
import logging
import requests
from slugify import slugify
from dbaas_credentials.models import CredentialType
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from networkapiclient import Ip, Network
from logical.validators import database_name_evironment_constraint
from logical.models import Database
from logical.forms import DatabaseForm
from dbaas.middleware import UserMiddleware
from util import get_credentials_for
from util.decorators import REDIS_CLIENT
from util import simple_health_check
from physical.models import Plan, Environment, PlanNotFound, Pool
from account.models import AccountUser, Team
from notification.models import TaskHistory
from notification.tasks import TaskRegister
from system.models import Configuration
from workflow.steps.util.base import ACLFromHellClient
from maintenance.models import DatabaseCreate
from django.utils.functional import cached_property

LOG = logging.getLogger(__name__)
DATABASE_NAME_REGEX = re.compile('^[a-z][a-z0-9_]+$')


class ListPlans(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Plan

    def get(self, request, format=None):
        hard_plans = Plan.objects.filter(
            environments__name=get_url_env(request)
        ).values(
            'name', 'description', 'environments__name'
        ).extra(
            where=['is_active=True', 'provider={}'.format(Plan.CLOUDSTACK)]
        )
        return Response(get_plans_dict(hard_plans))


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


class GetServiceInfo(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def get(self, request, database_name, format=None):
        env = get_url_env(request)
        try:
            database = get_database(database_name, env)
            info = {'used_size_in_bytes': str(database.used_size_in_bytes)}
        except IndexError as e:
            info = {}
            LOG.warn(
                "There is not a database {} on {}. {}".format(
                    database_name, env, e
                )
            )

        LOG.info("Info = {}".format(info))

        return Response(info)


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
                credential = database.credentials.all()[0]
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


class ServiceAdd(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    required_params = ('description', 'plan', 'user', 'name', 'team')
    search_metadata_params = ('plan', 'user', 'team', 'pool')
    model = Database

    def __init__(self, *args, **kw):
        super(ServiceAdd, self).__init__(*args, **kw)
        self.extra_params = {}

    @cached_property
    def data(self):
        data = self.request.DATA
        for k, v in data.iteritems():
            if k.startswith("parameters."):
                data.pop(k)
                data[k.replace('parameters.', '')] = v
        return data

    @property
    def description_param(self):
        return self.data.get('description')

    @property
    def name_param(self):
        return self.data.get('name')

    @property
    def user_param(self):
        return self.data.get('user')

    @property
    def dbaas_user(self):
        return AccountUser.objects.get(email=self.user_param)

    @property
    def team_param(self):
        return self.data.get('team')

    @property
    def dbaas_team(self):
        return Team.objects.get(name=self.team_param)

    @property
    def env_param(self):
        return get_url_env(self.request)

    @property
    def env(self):
        return Environment.objects.get(name=self.env_param)

    @property
    def is_k8s_env(self):
        k8s_envs = Configuration.get_by_name_as_list('k8s_envs')
        return self.env_param in k8s_envs

    @property
    def plan_param(self):
        return self.data.get('plan')

    @cached_property
    def dbaas_plan(self):
        hard_plans = Plan.objects.values(
            'name', 'description', 'pk', 'environments__name'
        ).extra(
            where=['is_active=True', 'provider={}'.format(Plan.CLOUDSTACK)]
        )
        plans = get_plans_dict(hard_plans)
        plan = [splan for splan in plans if splan['name'] == self.plan_param]

        if any(plan):
            return Plan.objects.get(pk=plan[0]['pk'])
        else:
            raise PlanNotFound("Plan was not found")

    @property
    def pool_param(self):
        return self.data.get('pool')

    @property
    def dbaas_pool(self):
        return Pool.objects.get(name=self.pool_param)

    def _validate_required_params(self):
        for param_name in self.required_params:
            param_value = self.data.get(param_name)
            if not param_value:
                msg = "Param {} must be provided.".format(param_name)
                return log_and_response(
                    msg=msg, http_status=status.HTTP_400_BAD_REQUEST
                )

    def _validate_search_metadata_params(self):
        """
            Search the field param on database.
            Ex. param user
            Search the username on database if does not found we return
            the error

        """
        for param_name in self.search_metadata_params:
            if param_name in self.data:
                try:
                    getattr(self, 'dbaas_{}'.format(param_name))
                except (ObjectDoesNotExist, PlanNotFound):
                    return log_and_response(
                        msg='{} <{}> was not found'.format(
                            param_name.capitalize(),
                            getattr(self, '{}_param'.format(param_name))
                        ),
                        http_status=status.HTTP_400_BAD_REQUEST
                    )

    def _validate_database(self):
        msg = ''
        if DATABASE_NAME_REGEX.match(self.name_param) is None:
            msg = "Your database name must match /^[a-z][a-z0-9_]+$/ ."
        try:
            Database.objects.get(
                name=self.name_param, environment__name=self.env_param
            )
            msg = "There is already a database called {} in {}.".format(
                self.name_param, self.env
            )
        except Database.DoesNotExist:
            pass
        if database_name_evironment_constraint(self.name_param, self.env):
            msg = "{} already exists in env {}!".format(
                self.name_param, self.env_param
            )
        if msg:
            return log_and_response(
                    msg=msg, http_status=status.HTTP_400_BAD_REQUEST
                )

    def _validate_user(self):
        msg = ''
        try:
            AccountUser.objects.get(email=self.user_param)
        except MultipleObjectsReturned as e:
            msg = "There are multiple user for {} email.".format(
                self.user_param
            )
        if msg:
            return log_and_response(
                    msg=msg, e=e, http_status=status.HTTP_400_BAD_REQUEST
                )

    def _validate_team(self):
        try:
            self.dbaas_user.team_set.get(name=self.team_param)
        except ObjectDoesNotExist as e:
            msg = "The user is not on {} team.".format(self.team_param)
            return log_and_response(
                msg=msg, e=e, http_status=status.HTTP_400_BAD_REQUEST
            )

    def _validate_env(self):
        try:
            self.env
        except ObjectDoesNotExist:
            msg = "Environment was not found"
            return log_and_response(
                msg=msg, http_status=status.HTTP_400_BAD_REQUEST
            )

    def _validate_database_alocation(self):
        databases_used_by_team = self.dbaas_team.count_databases_in_use(
            environment=self.env
        )
        database_alocation_limit = self.dbaas_team.database_alocation_limit

        if databases_used_by_team >= database_alocation_limit:
            msg = ("The database alocation limit of {} has been exceeded for "
                   "the selected team: {}").format(
                database_alocation_limit, self.dbaas_team
            )
            return log_and_response(
                msg=msg, http_status=status.HTTP_400_BAD_REQUEST
            )

    def _validate_plan(self):
        if self.env not in self.dbaas_plan.environments.all():
            msg = 'Plan "{}" is not available to "{}" environment'.format(
                self.dbaas_plan, self.env
            )
            return log_and_response(
                msg=msg, http_status=status.HTTP_400_BAD_REQUEST
            ), self.dbaas_plan

    def _validate_if_kubernetes_env(self):
        if self.is_k8s_env:
            if 'pool' not in self.data:
                msg = ("To create database on kubernetes you must pass the "
                       "pool name. Add the parameter "
                       "--plan-param pool=<POOL_NAME>")
                return log_and_response(
                    msg=msg, http_status=status.HTTP_400_BAD_REQUEST
                )
            if not self.dbaas_pool.teams.filter(name=self.team_param).exists():
                msg = "The Team <{}> arent on Pool <{}>".format(
                    self.team_param, self.pool_param
                )
                return log_and_response(
                    msg=msg, http_status=status.HTTP_400_BAD_REQUEST
                )
            self.extra_params.update({'pool': self.dbaas_pool})

    def post(self, request, format=None):
        err = self._validate_required_params()
        if err is not None:
            return err
        err = self._validate_search_metadata_params()
        if err is not None:
            return err
        err = self._validate_env()
        if err is not None:
            return err
        err = self._validate_database()
        if err is not None:
            return err
        err = self._validate_user()
        if err is not None:
            return err
        err = self._validate_team()
        if err is not None:
            return err
        err = self._validate_database_alocation()
        if err is not None:
            return err
        err = self._validate_plan()
        if err is not None:
            return err
        err = self._validate_if_kubernetes_env()
        if err is not None:
            return err

        backup_hour, maintenance_hour, maintenance_day = (
            DatabaseForm.randomize_backup_and_maintenance_hour()
        )

        TaskRegister.database_create(
            name=self.name_param,
            plan=self.dbaas_plan,
            environment=self.env,
            team=self.dbaas_team,
            project=None,
            description=self.description_param,
            user=self.dbaas_user,
            is_protected=True,
            backup_hour=backup_hour,
            maintenance_window=maintenance_hour,
            maintenance_day=maintenance_day,
            **self.extra_params
        )

        return Response(status=status.HTTP_201_CREATED)


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
                msg=msg, e=e, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    return Response("[DBaaS Error] {}".format(msg), http_status)


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


def get_database(name, env):
    if env in Configuration.get_by_name_as_list('dev_envs'):
        database = Database.objects.filter(
            name=name, environment__name=env
        ).exclude(is_in_quarantine=True)[0]
    else:
        prod_envs = Configuration.get_by_name_as_list('prod_envs')
        database = Database.objects.filter(
            name=name, environment__name__in=prod_envs
        ).exclude(is_in_quarantine=True)[0]

    return database


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
