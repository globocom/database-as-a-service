# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from errors import DatabaseInQuarantineError, DatabaseIsDeadError, \
    BusyDatabaseError, MigrationDatabaseError, NoResizeOption, \
    DatabaseWithoutPersistence


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

    if database.is_beeing_used_elsewhere():
        raise BusyDatabaseError(url)

    if database.has_flipperfox_migration_started():
        url = reverse('admin:logical_database_changelist')
        raise MigrationDatabaseError(operation, database.name, url)

    return database

def check_is_database_dead(database_id, operation):
    from logical.models import Database
    database = Database.objects.get(id=database_id)

    url = _get_database_error_url(database_id)
    if database.is_dead() or not database.database_status.is_alive:
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
