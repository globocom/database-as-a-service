# -*- coding: utf-8 -*-
from logical.models import Database
from django.core.exceptions import ObjectDoesNotExist
from system.models import Configuration


def database_name_evironment_constraint(database_name, environment_name):
    try:
        database = Database.objects.get(name=database_name)
    except ObjectDoesNotExist:
        return False
    else:
        dev_envs = Configuration.get_by_name_as_list('dev_envs')
        new_db_env_is_not_dev = environment_name not in dev_envs

        prod_envs = Configuration.get_by_name_as_list('prod_envs')
        db_env_is_prod = database.environment.name in prod_envs

        if new_db_env_is_not_dev and db_env_is_prod:
            return True
