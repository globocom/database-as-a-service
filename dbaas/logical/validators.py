# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from errors import DatabaseInQuarantineError, DatabaseIsDeadError, \
    BusyDatabaseError, MigrationDatabaseError, NoResizeOption, \
    DatabaseWithoutPersistence


class ParameterValidator(object):

    @classmethod
    def validate_value(cls, value, parameter):
        par_type = parameter.parameter_type

        if par_type == "" or par_type == "boolean":
            return True

        validate_function = getattr(cls, "validate_{}".format(par_type))

        return validate_function(value, parameter.allowed_values)

    @classmethod
    def validate_integer(cls, value, allowed_values):
        try:
            int(value)
        except ValueError:
            return False

        return cls.validate_number(value, allowed_values)

    @classmethod
    def validate_float(cls, value, allowed_values):
        if not '.' in value:
            return False

        return cls.validate_number(value, allowed_values)

    @classmethod
    def validate_number(cls, value, allowed_values):
        try:
            numeric = float(value)
        except ValueError:
            return False

        if allowed_values == "":
            return True

        allowed_values = allowed_values.split(',')
        for allowed_value in allowed_values:
            allowed_value = allowed_value.strip()
            try:
                if float(allowed_value) == float(value):
                    return True
            except ValueError:
                if cls.test_number_range(value, allowed_value):
                    return True

        return False
    
    @classmethod
    def test_number_range(cls, value, range):
        value = float(value)
        nums = range.split(':')
        lower_limit = float(nums[0])
        if nums[1] != "":
          upper_limit = float(nums[1])
          if value >= lower_limit and value <= upper_limit:
            return True  
        else:
            return value >= lower_limit

        return False

    @classmethod
    def validate_string(cls, value, allowed_values):

        if allowed_values == "":
            return True;

        allowed_set = allowed_values.split(',')
        for allowed_value in allowed_set:
            allowed_value = allowed_value.strip()
            if value == allowed_value:
                return True

        return False

def database_name_evironment_constraint(database_name, environment_name):
    from logical.models import Database
    from system.models import Configuration

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


def check_is_database_enabled(database_id, operation):
    from logical.models import Database
    database = Database.objects.get(id=database_id)

    url = _get_database_error_url(database_id)
    if database.is_in_quarantine:
        raise DatabaseInQuarantineError(operation, url)

    if database.is_being_used_elsewhere():
        raise BusyDatabaseError(url)

    return database

def check_is_database_dead(database_id, operation):
    from logical.models import Database
    database = Database.objects.get(id=database_id)

    url = _get_database_error_url(database_id)
    if database.is_dead:
        raise DatabaseIsDeadError(operation, url)

    return database


def check_resize_options(database_id, offerings):
    if not offerings:
        raise NoResizeOption(_get_database_error_url(database_id))


def check_database_has_persistence(database, operation):
    if not database.plan.has_persistence:
        raise DatabaseWithoutPersistence(
            database, operation, _get_database_error_url(database.id)
        )

def _get_database_error_url(database_id):
    return reverse('admin:logical_database_change', args=[database_id])
