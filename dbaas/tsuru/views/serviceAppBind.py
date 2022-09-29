from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from logical.models import Database
from workflow.steps.util.base import ACLFromHellClient
from ..utils import (log_and_response, get_url_env, LOG, check_database_status, check_maintenance)
from rest_framework import status


class AclFromHellNotAllowerForEnvException(Exception):
    pass


class ServiceAppBind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def add_acl_for_hosts(self, database, app_name):

        infra = database.infra
        hosts = infra.hosts

        acl_from_hell_client = ACLFromHellClient(database.environment)
        if not acl_from_hell_client.aclfromhell_allowed:
            raise AclFromHellNotAllowerForEnvException(
                "ACL from hell credential not found for env {}".format(
                    database.environment
                )
            )

        for host in hosts:
            acl_from_hell_client.add_acl(database, app_name, host.hostname)
        acl_from_hell_client.add_acl_for_vip_if_needed(database, app_name)

    @staticmethod
    def _handle_app_name(app_name):
        return app_name[0] if isinstance(app_name, list) else app_name

    @check_maintenance
    def post(self, request, database_name, format=None):
        """This method binds a App to a database through tsuru."""
        env = get_url_env(request)
        data = request.DATA
        LOG.debug("Tsuru Bind App POST Request DATA {}".format(data))

        response = check_database_status(database_name, env)
        if not isinstance(response, self.model):
            return response

        database = response
        try:
            self.add_acl_for_hosts(
                database,
                self._handle_app_name(data['app-name'])
            )
        except Exception as e:
            return log_and_response(str(e))

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

    @check_maintenance
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
