import re
import logging
from slugify import slugify
from logical.models import Database
from physical.models import Environment
from rest_framework.response import Response


LOG = logging.getLogger(__name__)
DATABASE_NAME_REGEX = re.compile('^[a-z][a-z0-9_]+$')


def get_database(name, env):
    query_params = {
        'name': name
    }

    environments = Environment.prod_envs()\
        if env in Environment.prod_envs() else Environment.dev_envs()
    query_params['environment__name__in'] = environments

    return Database.objects.filter(
        **query_params
    ).exclude(is_in_quarantine=True)[0]


def get_url_env(request):
    return request._request.path.split('/')[1]


def get_plans_dict(hard_plans):
    plans = []
    for hard_plan in hard_plans:
        hard_plan['description'] = '%s - %s\n%s' % (
            hard_plan['name'],
            hard_plan['environments__name'],
            hard_plan['environments__location_description'] or ""
        )
        hard_plan['name'] = slugify("%s - %s" % (
            hard_plan['description'],
            hard_plan['environments__name'],
        ))
        del hard_plan['environments__name']
        del hard_plan['environments__location_description']
        plans.append(hard_plan)

    return plans


def log_and_response(msg, http_status=400, e="Conditional Error."):
    LOG.warn(msg)
    LOG.warn("Error: {}".format(e))
    return Response("[DBaaS Error] {}".format(msg), http_status)


def validate_environment(request):
    return get_url_env(request) in\
        (list(Environment.prod_envs()) + list(Environment.dev_envs()))


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
