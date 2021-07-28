from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from logical.models import Database
from physical.models import Plan, Environment, PlanNotFound
from rest_framework import status
from utils import (get_plans_dict, get_url_env,
                   log_and_response, validate_environment,
                   LOG, DATABASE_NAME_REGEX)
from django.utils.functional import cached_property
from django.core.exceptions import ObjectDoesNotExist
from account.models import AccountUser, Team
from logical.validators import database_name_evironment_constraint
from logical.forms import DatabaseForm
from notification.tasks import TaskRegister


class ServiceAdd(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    required_params = ('description', 'plan', 'user', 'name', 'team')
    search_metadata_params = ('plan', 'user', 'team')
    model = Database
    tsuru_pool_name_header = 'HTTP_X_TSURU_POOL_NAME'
    tsuru_pool_endpoint_header = 'HTTP_X_TSURU_CLUSTER_ADDRESSES'

    def __init__(self, *args, **kw):
        super(ServiceAdd, self).__init__(*args, **kw)
        self.extra_params = {}

    @cached_property
    def data(self):
        return self.request.DATA

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
        k8s_envs = Environment.k8s_envs()
        return self.env_param in k8s_envs

    @property
    def plan_param(self):
        return self.data.get('plan')

    @property
    def stage(self):
        return Environment.DEV if\
            self.env_param in Environment.dev_envs() else\
            Environment.PROD

    @cached_property
    def dbaas_plan(self):
        hard_plans = Plan.objects.filter(
            environments__stage=self.stage,
            is_active=True,
            environments__tsuru_deploy=True
        ).values(
            'name', 'id', 'environments__name',
            'environments__location_description'
        )
        plans = get_plans_dict(hard_plans)
        plan = [splan for splan in plans if splan['name'] == self.plan_param]

        if any(plan):
            return Plan.objects.get(pk=plan[0]['id'])
        else:
            raise PlanNotFound("Plan was not found")

    @property
    def pool_param(self):
        return self.request.META.get(self.tsuru_pool_name_header)

    @property
    def pool_endpoint_param(self):
        return self.request.META.get(self.tsuru_pool_endpoint_header)

    @property
    def dbaas_pool(self):
        return Pool.objects.get(
            cluster_endpoint=self.pool_endpoint_param
        )

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
        try:
            AccountUser.objects.get(email=self.user_param)
        except MultipleObjectsReturned as e:
            msg = "There are multiple user for {} email.".format(
                self.user_param
            )
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
            if not validate_environment(self.request):
                raise EnvironmentError
        except (ObjectDoesNotExist, EnvironmentError):
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
        ''' Plan stage needs to be equal
            the env stage'''
        for e in self.dbaas_plan.environments.all():
            if e.stage == self.stage:
                return None

        msg = 'Plan "{}" is not available to "{}" environment'.format(
            self.dbaas_plan, self.env
        )
        return log_and_response(
            msg=msg, http_status=status.HTTP_400_BAD_REQUEST
        )

    def _validate_if_kubernetes_env(self):
        LOG.info("Tsuru Debug headers:{}".format(self.request.META))
        if self.is_k8s_env:
            if not self.pool_param:
                msg = ("the header <{}> was not found "
                       "on headers. Contact tsuru team.".format(
                           self.tsuru_pool_name_header
                       ))
                return log_and_response(
                    msg=msg, http_status=status.HTTP_400_BAD_REQUEST
                )
            if not self.pool_endpoint_param:
                msg = (
                    "the header <{}> "
                    "was not found on headers. Contact tsuru team.".format(
                        self.tsuru_pool_endpoint_header
                    )
                )
                return log_and_response(
                    msg=msg, http_status=status.HTTP_400_BAD_REQUEST
                )
            if not self.pool_endpoint_param:
                msg = (
                    "the header <HTTP_X_TSURU_CLUSTER_ADDRESS> "
                    "was not found on headers. Contact tsuru team."
                )
                return log_and_response(
                    msg=msg, http_status=status.HTTP_400_BAD_REQUEST
                )
            try:
                self.dbaas_pool
            except Pool.DoesNotExist:
                msg = (
                    "Pool with name <{}> and endpoint <{}> was not found"
                ).format(
                    self.pool_param,
                    self.pool_endpoint_param
                )
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
