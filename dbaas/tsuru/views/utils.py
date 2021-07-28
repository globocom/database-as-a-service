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
