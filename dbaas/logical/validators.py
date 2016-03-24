# -*- coding: utf-8 -*-
from system.models import Configuration


def database_name_evironment_constraint(database_name, environment_name):
    from logical.models import Database

    databases = Database.objects.filter(name=database_name)
    if not databases:
        return False

    dev_envs = Configuration.get_by_name_as_list('dev_envs')
    if environment_name in dev_envs:
        return False

    prod_envs = Configuration.get_by_name_as_list('prod_envs')
    return any((
        database.environment.name in prod_envs
        for database in databases))
