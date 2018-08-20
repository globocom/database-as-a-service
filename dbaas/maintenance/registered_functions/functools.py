import sys
import inspect
import logging
from django.core.exceptions import ObjectDoesNotExist

LOG = logging.getLogger(__name__)


def _is_mod_function(mod, func):
    return inspect.isfunction(func) and inspect.getmodule(func) == mod


def _get_key(item):
    return item[1]


def _get_registered_functions():
    current_module = sys.modules[__name__]
    function_list = ((func.__name__, func.__doc__) for func in current_module.__dict__.itervalues()
                     if _is_mod_function(current_module,
                                         func) and not func.__name__.startswith('_'))

    return sorted(function_list, key=_get_key)


def get_function(func_name):
    current_module = sys.modules[__name__]
    func_list = list((func for func in current_module.__dict__.itervalues()
                      if _is_mod_function(current_module, func) and func.__name__ == func_name))

    try:
        func_list = func_list[0]
    except IndexError as e:
        LOG.info("Function not found! {}".format(e))
        return None

    return func_list


def get_hostmane(host_id):
    """Return HOST_NAME"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.hostname
    except Exception as e:
        LOG.warn("Error on get_hostmane. Host id: {} - error: {}".format(host_id, e))
        return None


def get_hostaddress(host_id):
    """Return HOST_ADDRESS"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.address
    except Exception as e:
        LOG.warn("Error on get_hostaddress. Host id: {} - error: {}".format(host_id, e))
        return None


def get_infra_name(host_id):
    """Return DATABASE_INFRA_NAME"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.instances.all()[0].databaseinfra.name
    except Exception as e:
        LOG.warn("Error on get_infra_name. Host id: {} - error: {}".format(host_id, e))
        return None


def get_database_name(host_id):
    """Return DATABASE_NAME"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        database = host.instances.all()[0].databaseinfra.databases.all()[0]
        return database.name
    except Exception as e:
        LOG.warn("Error on get_database_name. Host id: {} - error: {}".format(host_id, e))
        return None


def get_infra_user(host_id):
    """Return DATABASE_INFRA_USER"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.instances.all()[0].databaseinfra.user
    except Exception as e:
        LOG.warn("Error on get_infra_user. Host id: {} - error: {}".format(host_id, e))
        return None


def get_infra_password(host_id):
    """Return DATABASE_INFRA_PASSWORD"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.instances.all()[0].databaseinfra.password
    except Exception as e:
        LOG.warn("Error on get_infra_password. Host id: {} - error: {}".format(host_id, e))
        return None


def get_host_user(host_id):
    """Return HOST_USER"""
    from physical.models import Host

    try:
        host = Host.objects.get(id=host_id)
    except Host.DoesNotExist as e:
        LOG.warn("Host id does not exists: {}. {}".format(host_id, e))
    else:
        return host.user


def get_host_password(host_id):
    """Return HOST_PASSWORD"""
    from physical.models import Host

    try:
        host = Host.objects.get(id=host_id)
    except Host.DoesNotExist as e:
        LOG.warn("Host id does not exists: {}. {}".format(host_id, e))
    else:
        return host.password


def get_engine_type_name(host_id):
    """Return ENGINE_TYPE"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.instances.all()[0].databaseinfra.engine.name
    except Exception as e:
        LOG.warn("Error on get_engine_type_name. Host id: {} - error: {}".format(host_id, e))
        return None


def get_max_database_size(host_id):
    """Return MAX_DATABASE_SIZE"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.instances.all()[0].databaseinfra.plan.max_db_size
    except Exception as e:
        LOG.warn("Error on get_max_database_size. Host id: {} - error: {}".format(host_id, e))
        return None


def get_offering_size(host_id):
    """Return OFFERING_SIZE"""
    from physical.models import Host
    try:
        host = Host.objects.get(id=host_id)
        return host.instances.all()[0].databaseinfra.cs_dbinfra_offering.get().offering.memory_size_mb
    except Exception as e:
        LOG.warn("Error on get_offering_size. Host id: {} - error: {}".format(host_id, e))
        return None
