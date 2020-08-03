import logging
from util import get_credentials_for
from util import get_replication_topology_instance
from dbaas_credentials.models import CredentialType


LOG = logging.getLogger(__name__)


def get_deploy_settings(class_path):
    return get_replication_topology_instance(class_path).get_deploy_steps()


def get_destroy_settings(class_path):
    return get_replication_topology_instance(class_path).get_destroy_steps()


def get_deploy_instances(class_path):
    return get_replication_topology_instance(class_path).deploy_instances()


def get_clone_settings(class_path):
    return get_replication_topology_instance(class_path).get_clone_steps()


def get_resize_settings(class_path):
    return get_replication_topology_instance(class_path).get_resize_steps()


def get_restore_snapshot_settings(class_path):
    return get_replication_topology_instance(class_path).get_restore_snapshot_steps()


def get_database_upgrade_setting(class_path):
    return get_replication_topology_instance(class_path).get_upgrade_steps()


def get_engine_migrate_settings(class_path):
    return get_replication_topology_instance(
        class_path
    ).get_migrate_engines_steps()


def get_database_upgrade_patch_setting(class_path):
    return get_replication_topology_instance(class_path).get_upgrade_patch_steps()


def get_reinstallvm_steps_setting(class_path):
    return get_replication_topology_instance(class_path).get_reinstallvm_steps()


def get_database_configure_ssl_setting(class_path):
    return get_replication_topology_instance(class_path).get_configure_ssl_steps()


def get_database_change_parameter_setting(class_path, all_dinamic, custom_procedure):
    replication_topology = get_replication_topology_instance(class_path)
    if custom_procedure:
        custom_proc_method = getattr(replication_topology, custom_procedure)
        return custom_proc_method()[0]
    elif all_dinamic:
        return replication_topology.get_change_dinamic_parameter_steps()
    else:
        return replication_topology.get_change_static_parameter_steps()


def get_database_change_parameter_retry_steps_count(class_path, all_dinamic, custom_procedure):
    replication_topology = get_replication_topology_instance(class_path)

    if custom_procedure:
        custom_proc_method = getattr(replication_topology, custom_procedure)
        return custom_proc_method()[1]
    elif all_dinamic:
        return replication_topology.get_change_dinamic_parameter_retry_steps_count()
    else:
        return replication_topology.get_change_static_parameter_retry_steps_count()


def get_add_database_instances_steps(class_path):
    return get_replication_topology_instance(class_path).get_add_database_instances_steps()


def get_remove_readonly_instance_steps(class_path):
    return get_replication_topology_instance(class_path).get_remove_readonly_instance_steps()


def get_switch_write_instance_steps(class_path):
    return get_replication_topology_instance(class_path).get_switch_write_instance_steps()


def get_filer_migrate_steps(class_path):
    return get_replication_topology_instance(class_path).get_filer_migrate_steps()


def get_host_migrate_steps(class_path):
    return get_replication_topology_instance(class_path).get_host_migrate_steps()


def get_database_migrate_steps(class_path):
    return get_replication_topology_instance(class_path).get_database_migrate_steps()


def get_database_change_persistence_setting(class_path):
    return get_replication_topology_instance(class_path).get_database_change_persistence_steps()


def get_engine_credentials(engine, environment):
    engine = engine.lower()

    if engine.startswith('mongo'):
        credential_type = CredentialType.MONGODB
    elif engine.startswith(('mysql', 'redis')):
        credential_type = CredentialType.MYSQL

    return get_credentials_for(
        environment=environment,
        credential_type=credential_type
    )
