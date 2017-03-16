# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr
from util import get_credentials_for
from util import build_context_script
from util import exec_remote_command
from dbaas_credentials.models import CredentialType
from dbaas_foxha.provider import FoxHAProvider
from dbaas_foxha.dbaas_api import DatabaseAsAServiceApi
from base import BaseTopology

LOG = logging.getLogger(__name__)


class BaseMysql(BaseTopology):
    def deploy_first_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_secondary_ip.CreateSecondaryIp',
            'workflow.steps.mysql.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.create_flipper.CreateFlipper',
            'workflow.steps.mysql.deploy.init_database.InitDatabase',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def get_clone_steps(self):
        return self.deploy_first_steps() + self.deploy_last_steps() + (
            'workflow.steps.util.clone.clone_database.CloneDatabase',
            'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
        ) + self.monitoring_steps()

    def switch_master(self, driver):
        raise NotImplementedError()

    def check_instance_is_master(self, driver, instance):
        raise NotImplementedError

    def set_master(self, driver, instance):
        raise NotImplementedError

    def set_read_ip(self, driver, instance):
        raise NotImplementedError

    def get_database_agents(self):
        return ['monit']


class MySQLSingle(BaseMysql):

    def switch_master(self, driver):
        return True

    def check_instance_is_master(self, driver, instance):
        return True

    def set_master(self, driver, instance):
        raise True

    def set_read_ip(self, driver, instance):
        raise True


class MySQLFlipper(BaseMysql):

    def get_restore_snapshot_steps(self):
        return (
            'workflow.steps.mysql.restore_snapshot.restore_snapshot.RestoreSnapshot',
            'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
            'workflow.steps.mysql.restore_snapshot.stop_database.StopDatabase',
            'workflow.steps.mysql.restore_snapshot.umount_data_volume.UmountDataVolume',
            'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
            'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
            'workflow.steps.mysql.restore_snapshot.start_database_and_replication.StartDatabaseAndReplication',
            'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
            'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
            'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
        )

    def switch_master(self, driver):
        master = driver.get_master_instance()
        slave = driver.get_slave_instances()[0]
        host = master.hostname

        host_attr = HostAttr.objects.get(host=host)

        script = """
        sudo -u flipper /usr/bin/flipper {{MASTERPAIRNAME}} set write {{HOST01.address}}
        sudo -u flipper /usr/bin/flipper {{MASTERPAIRNAME}} set read {{HOST02.address}}
        """

        context_dict = {
            'MASTERPAIRNAME': driver.databaseinfra.name,
            'HOST01': slave.hostname,
            'HOST02': master.hostname,
        }
        script = build_context_script(context_dict, script)
        output = {}

        return_code = exec_remote_command(
            server=host.address, username=host_attr.vm_user,
            password=host_attr.vm_password, command=script, output=output
        )

        LOG.info(output)
        if return_code != 0:
            raise Exception(str(output))

    def set_master(self, driver, instance):
        command = """
            echo ""; echo $(date "+%Y-%m-%d %T") "- Setting flipper IPs"
            sudo -u flipper /usr/bin/flipper {infra_name} ipdown write
            sudo -u flipper /usr/bin/flipper {infra_name} set write {master_host}
        """

        command = command.format(infra_name=driver.databaseinfra.name,
                                 master_host=instance.address)

        cs_host_attr = HostAttr.objects.get(host=instance.hostname)

        output = {}
        return_code = exec_remote_command(server=instance.address,
                                          username=cs_host_attr.vm_user,
                                          password=cs_host_attr.vm_password,
                                          command=command,
                                          output=output)

        if return_code != 0:
            raise Exception("Could not Change WriteIP: {}".format(output))

        return True

    def set_read_ip(self, driver, instance):
        command = """
            echo ""; echo $(date "+%Y-%m-%d %T") "- Setting flipper IPs"
            sudo -u flipper /usr/bin/flipper {infra_name} ipdown read
            sudo -u flipper /usr/bin/flipper {infra_name} set read {slave_host}
        """

        command = command.format(infra_name=driver.databaseinfra.name,
                                 slave_host=instance.address)

        cs_host_attr = HostAttr.objects.get(host=instance.hostname)

        output = {}
        return_code = exec_remote_command(server=instance.address,
                                          username=cs_host_attr.vm_user,
                                          password=cs_host_attr.vm_password,
                                          command=command,
                                          output=output)

        if return_code != 0:
            raise Exception("Could not Change ReadIP: {}".format(output))

        return True

    def check_instance_is_master(self, driver, instance):
        results = driver.query(
            query_string="show variables like 'read_only'", instance=instance
        )
        if results[0]["Value"] == "ON":
            return False
        else:
            return True

    def get_database_agents(self):
        agents = ['httpd', 'mk-heartbeat-daemon']
        return super(MySQLFlipper, self).get_database_agents() + agents


class MySQLFoxHA(MySQLSingle):

    def get_restore_snapshot_steps(self):
        return (
            'workflow.steps.mysql.restore_snapshot.restore_snapshot.RestoreSnapshot',
            'workflow.steps.util.restore_snapshot.grant_nfs_access.GrantNFSAccess',
            'workflow.steps.mysql.restore_snapshot.stop_database.StopDatabase',
            'workflow.steps.mysql.restore_snapshot.umount_data_volume.UmountDataVolume',
            'workflow.steps.util.restore_snapshot.update_fstab.UpdateFstab',
            'workflow.steps.util.restore_snapshot.mount_data_volume.MountDataVolume',
            'workflow.steps.mysql.restore_snapshot.start_database_and_replication.StartDatabaseAndReplication',
            'workflow.steps.util.restore_snapshot.make_export_snapshot.MakeExportSnapshot',
            'workflow.steps.util.restore_snapshot.update_dbaas_metadata.UpdateDbaaSMetadata',
            'workflow.steps.util.restore_snapshot.clean_old_volumes.CleanOldVolumes',
        )

    def deploy_first_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mysql.deploy.create_virtualmachines_fox.CreateVirtualMachine',
            'workflow.steps.mysql.deploy.create_vip.CreateVip',
            'workflow.steps.mysql.deploy.create_dns_foxha.CreateDnsFoxHA',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mysql.deploy.init_database_foxha.InitDatabaseFoxHA',
            'workflow.steps.mysql.deploy.check_pupet.CheckPuppetIsRunning',
            'workflow.steps.mysql.deploy.config_vms_foreman.ConfigVMsForeman',
            'workflow.steps.mysql.deploy.run_pupet_setup.RunPuppetSetup',
            'workflow.steps.mysql.deploy.config_fox.ConfigFox',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def get_resize_extra_steps(self):
        return (
            'workflow.steps.util.database.StartSlave',
        ) + super(BaseMysql, self).get_resize_extra_steps()

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def _get_fox_provider(self, driver):
        databaseinfra = driver.databaseinfra

        foxha_credentials = get_credentials_for(
            environment=databaseinfra.environment,
            credential_type=CredentialType.FOXHA
        )
        dbaas_api = DatabaseAsAServiceApi(databaseinfra, foxha_credentials)
        return FoxHAProvider(dbaas_api)

    def switch_master(self, driver):
        self._get_fox_provider(driver).switchover(
            group_name=driver.databaseinfra.name
        )

    def check_instance_is_master(self, driver, instance):
        return self._get_fox_provider(driver).node_is_master(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def set_master(self, driver, instance):
        self._get_fox_provider(driver).set_master(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def set_read_ip(self, driver, instance):
        self._get_fox_provider(driver).set_read_only(
            group_name=driver.databaseinfra.name,
            node_ip=instance.address
        )

    def get_database_agents(self):
        agents = ['httpd', '/etc/init.d/pt-heartbeat']
        return super(MySQLFoxHA, self).get_database_agents() + agents

    def add_database_instances_first_steps(self):
        return ()

    def add_database_instances_last_steps(self):
        return ()
