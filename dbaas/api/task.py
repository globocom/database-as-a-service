# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from rest_framework import viewsets, serializers, permissions
from rest_framework import filters

from notification.models import TaskHistory
from logical.models import Database, DatabaseHistory


class TaskSerializer(serializers.ModelSerializer):
    database = serializers.SerializerMethodField('get_database')
    rollback = serializers.SerializerMethodField('had_rollback')
    relevance = serializers.SerializerMethodField('get_relevance')

    class Meta:
        model = TaskHistory
        fields = (
            'id',
            'task_id',
            'task_status',
            'db_id',
            'object_class',
            'object_id',
            'updated_at',
            'user',
            'created_at',
            'task_name',
            'database',
            'database_name',
            'rollback',
            'relevance',
            'ended_at',
        )

    def get_relevance(self, task):
        return task.get_relevance_display()

    def had_rollback(self, task):
        if not task.details:
            return False

        if task.task_name == 'notification.tasks.destroy_database':
            return False

        # TODO: see if do details.lower() is expensive
        return 'rollback step' in task.details.lower()

    def get_database(self, task):
        def make_dict_from_model(instance):
            engine = instance.databaseinfra.engine
            return {
                'name': instance.name,
                'environment': instance.environment.name,
                'engine': '{} {}'.format(
                    engine.engine_type.name,
                    engine.version
                )
            }

        def make_dict_from_history(instance):
            return {
                'name': instance.name,
                'environment': instance.environment,
                'engine': instance.engine
            }

        if task.object_class == Database._meta.db_table:
            try:
                database = (
                    Database.objects
                    .select_related(
                        'environment',
                        'databaseinfra',
                        'databaseinfra__engine',
                        'databaseinfra__engine__enginetype'
                    ).get(id=task.object_id)
                )
            except Database.DoesNotExist:
                try:
                    database_history = DatabaseHistory.objects.get(
                        database_id=task.object_id
                    )
                except DatabaseHistory.DoesNotExist:
                    return None
                except DatabaseHistory.MultipleObjectsReturned:
                    return make_dict_from_history(
                        DatabaseHistory.objects.filter(
                            database_id=task.object_id
                        ).last()
                    )
                else:
                    return make_dict_from_history(database_history)
            else:
                return make_dict_from_model(database)

        return None


class TaskAPI(viewsets.ReadOnlyModelViewSet):

    """
    Task API
    """
    all_chg_tasks_names = [
        'maintenance.tasks.create_database_rollback',
        'maintenance.tasks.database_environment_migrate_rollback',
        'maintenance.tasks.node_zone_migrate_rollback',
        'maintenance.tasks.region_migrate',
        'maintenance.tasks.region_migrate_rollback',
        'maintenance.tasks.restore_database',
        'maintenance.tasks.rollback_create_database',
        'maintenance.tasks.start_database_vm',
        'maintenance.tasks.stop_database_vm',
        'host_migrate',
        'maintenance.tasks.update_ssl',
        'maintenance.tasks.update_ssl_rollback',
        'maintenance.tasks.upgrade_disk_type_database',
        'make_database_backup',
        'migrating_filer',
        'migrating_zone',
        'notification.tasks.add_instances_to_database_rollback',
        'notification.tasks.change_mongodb_log_rotate',
        'notification.tasks.change_parameters_database',
        'notification.tasks.clone_database_rollback',
        'notification.tasks.configure_ssl_database',
        'notification.tasks.database_set_ssl_not_required',
        'notification.tasks.database_set_ssl_required',
        'notification.tasks.destroy_database_retry',
        'notification.tasks.resize_database_rollback',
        'notification.tasks.resize_database_retry',
        'notification.tasks.switch_write_database',
        'region_migration.tasks.execute_database_region_migration',
        'region_migration.tasks.execute_database_region_migration_undo',
        'resize_disk_from_zabbix_alert',
        'switch_masters_in_zone',
        'update_config_files',
        'database_quarantine',
    ]

    chg_tasks_names = [
        'notification.tasks.destroy_database',
        'notification.tasks.create_database',
        'notification.tasks.resize_database',
        'notification.tasks.clone_database',
        'notification.tasks.database_disk_resize',
        'notification.tasks.add_instances_to_database',
        'notification.tasks.remove_readonly_instance',
        'database_disk_resize',
        'backup.tasks.restore_snapshot',
        'notification.tasks.upgrade_mongodb_24_to_30',
        'notification.tasks.upgrade_database',
        'notification.tasks.upgrade_database_patch',
        'notification.tasks.reinstall_vm_database',
        'migrate_filer_disk_for_database',
        'maintenance.tasks.node_zone_migrate',
        'maintenance.tasks.database_environment_migrate',
        'maintenance.tasks.recreate_slave',
        'notification.tasks.migrate_engine',
        'maintenance.tasks.restart_database',
        'notification.tasks.change_database_persistence',
        'maintenance.tasks.task_upgrade_disk_type',
        'maintenance.tasks.auto_upgrade_database_vm_offering',
    ]

    model = TaskHistory
    serializer_class = TaskSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.OrderingFilter,)
    filter_fields = (
        'task_id',
        'task_status',
        'task_name',
        'object_class',
        'object_id',
        'updated_at',
        'created_at',
        'user',
        'relevance',
        'ended_at',
        'database_name'
    )
    ordering_fields = ('created_at', 'updated_at', 'id')
    ordering = ('-created_at',)
    datetime_fields = ('created_at', 'updated_at', 'ended_at')

    def get_queryset(self):
        params = self.request.GET.dict()
        database = Database.objects.all()

        filter_params = {}
        for k, v in params.iteritems():
            if k == 'exclude_system_tasks':
                filter_params['task_name__in'] = self.chg_tasks_names
            elif k.split('__')[0] in self.filter_fields:
                filter_params[k] = v
        result = self.model.objects.filter(**filter_params)

        database_name_list = [
            db.name
            for db in database
            if db.send_all_chg
        ]

        if database_name_list:
            filter_param_chg = {
                'task_name__in': self.chg_tasks_names + self.all_chg_tasks_names,
                'database_name__in': database_name_list
            }
            for key, value in params.iteritems():
                if key not in ['exclude_system_tasks', 'database_name'] and key.split('__')[0] in self.filter_fields:
                    filter_param_chg[key] = value
            result_chg = self.model.objects.filter(**filter_param_chg)
            return (result_chg | result).order_by('updated_at')
        return result
