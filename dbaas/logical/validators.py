# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from logical.models import Database
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from system.models import Configuration


def validate_evironment(database_name, environment_name):
    try:
        database = Database.objects.get(database_name)
    except ObjectDoesNotExist:
        pass
    else:
        dev_envs = Configuration.get_by_name_as_list('dev_envs')
        new_db_env_is_not_dev = environment_name not in dev_envs

        prod_envs = Configuration.get_by_name_as_list('prod_envs')
        db_env_is_prod = database.environment.name in prod_envs

        if new_db_env_is_not_dev and db_env_is_prod:
            raise ValidationError(
                _('%(database_name)s already exists in production!'),
                params={'database_name': database_name},
            )
