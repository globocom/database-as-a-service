import sys, inspect
import logging
LOG = logging.getLogger(__name__)

def is_mod_function(mod, func):
    return inspect.isfunction(func) and inspect.getmodule(func) == mod

def get_registered_functions():
    current_module = sys.modules[__name__]
    return ((func.__name__, func.__doc__) for func in current_module.__dict__.itervalues()
            if is_mod_function(current_module,
                func) and func.__name__ not in['is_mod_function','get_registered_functions','get_function', ])

def get_function(func_name):
    current_module = sys.modules[__name__]
    func_list =  list((func for func in current_module.__dict__.itervalues()
            if is_mod_function(current_module,func) and func.__name__ ==func_name))

    try:
        func_list = func_list[0]
    except IndexError, e:
        LOG.info("Function not found! {}".format(e))
        return None

    return func_list


def return_host_id_str(host_id):
    """Get HostId String"""
    return str(host_id)

def get_hostmane(host_id):
    """Return HOSTNAME"""
    from physical.models import Host
    host = Host.objects.get(id=host_id)
    return host.hostname


