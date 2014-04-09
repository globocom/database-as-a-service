# -*- coding: utf-8 -*-
from cloudstack_client import CloudStackClient
from django.db import transaction
from physical.models import DatabaseInfra, Instance, Host
from util import make_db_random_password
from drivers import factory_for
from .models import PlanAttr, HostAttr
from ..base import BaseProvider
from base64 import b64encode
import logging
from integrations.storage.manager import StorageManager
from django.template import Context, Template
from time import sleep
import paramiko
import socket


LOG = logging.getLogger(__name__)

class CloudStackProvider(BaseProvider):

    @classmethod
    def get_credentials(self, environment):
        LOG.info("Getting credentials...")
        from integrations.credentials.manager import IntegrationCredentialManager
        from integrations.credentials.models import IntegrationType
        integration = IntegrationType.objects.get(type= IntegrationType.CLOUDSTACK)

        return IntegrationCredentialManager.get_credentials(environment= environment, integration= integration)

    @classmethod
    def auth(self, environment):
        LOG.info("Conecting with cloudstack...")
        credentials = self.get_credentials(environment= environment)
        return CloudStackClient(credentials.endpoint, credentials.token, credentials.secret)

        
    @classmethod
    @transaction.commit_on_success
    def destroy_instance(self, database, *args, **kwargs):
        from logical.models import Credential, Database

        LOG.warning("Deleting the host on cloud portal...")

        if database.is_in_quarantine:
            host = database.databaseinfra.instances.all()[0].hostname
            host_attr = HostAttr.objects.filter(host= host)[0]
            super(Database, database).delete(*args, **kwargs)  # Call the "real" delete() method.
            
            LOG.info("Remove all database files")
            self.run_script(host, "/opt/dbaas/scripts/dbaas_deletedatabasefiles.sh")
            
            plan = database.databaseinfra.plan            
            environment = database.databaseinfra.environment
            
            LOG.info("Destroying storage (environment:%s, plan: %s, host:%s)!" % (environment, plan, host))
            StorageManager.destroy_disk(environment=environment, plan=plan, host=host)
            
            
            project_id = self.get_credentials(environment= environment).project

            api = self.auth(environment= environment)
            request = {  'projectid': '%s' % (project_id),
                               'id': '%s' % (host_attr.vm_id)
                            }
            response = api.destroyVirtualMachine('GET',request)
            
            try:
                if response['jobid']:
                    LOG.warning("VirtualMachine destroyed!")

                    instance = Instance.objects.get(hostname=host)
                    databaseinfra = DatabaseInfra.objects.get(instances=instance)

                    databaseinfra.delete()
                    LOG.info("DatabaseInfra destroyed!")
                    instance.delete
                    LOG.info("Instance destroyed!")
                    host_attr.delete()
                    LOG.info("Host custom cloudstack attrs destroyed!")
                    host.delete()
                    LOG.info("Host destroyed!")
                    paramiko.HostKeys().clear()
                    LOG.info("Removing key from known hosts!")
                    LOG.info("Finished!")
            except (KeyError, LookupError):
                LOG.warning("We could not destroy the VirtualMachine. :(")
        else:
            LOG.warning("Putting database %s in quarantine" % database.name)
            database.is_in_quarantine=True
            database.save()
            if database.credentials.exists():
                for credential in database.credentials.all():
                    new_password = make_db_random_password()
                    new_credential = Credential.objects.get(pk=credential.id)
                    new_credential.password = new_password
                    new_credential.save()

                    instance = factory_for(database.databaseinfra)
                    instance.update_user(new_credential)

    @classmethod
    def run_script(self, host, command):
        host_attr = HostAttr.objects.filter(host= host)[0]

        username = host_attr.vm_user
        password = host_attr.vm_password
        
        LOG.info("Running script [%s] on host %s" % (command, host))
        
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host.hostname, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        
        log_stdout = stdout.readlines()
        log_stderr = stderr.readlines()
        cod_ret_start = stdout.channel.recv_exit_status()
        
        LOG.info("Script return code: %s, stdout: %s, stderr %s" % (cod_ret_start, log_stdout, log_stderr))
        return cod_ret_start
        

    @classmethod
    def check_ssh(self, host, retries=6, initial_wait=30, interval=40):
        host_attr = HostAttr.objects.filter(host= host)[0]

        username = host_attr.vm_user
        password = host_attr.vm_password
        ssh = paramiko.SSHClient()
        port=22
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        LOG.info("Waiting %s seconds to check %s ssh connection..." % (initial_wait, host.hostname))
        sleep(initial_wait)

        for x in range(retries):
            try:
                LOG.info("Login attempt number %i on %s " % (x+1,host.hostname))
                ssh.connect(host.hostname, port=port, 
                                    username=username, password=password, 
                                    timeout= None, allow_agent= True, 
                                    look_for_keys= True, compress= False
                                    )
                return True
            except (paramiko.ssh_exception.BadHostKeyException, 
                        paramiko.ssh_exception.AuthenticationException, 
                        paramiko.ssh_exception.SSHException, socket.error) as e:
                LOG.warning("We caught an exception: %s ." % (e))
                LOG.info("Wating %i seconds to try again..." % ( interval + 30))
                sleep(interval)
                sleep(30)
            finally:
                ssh.close()


    @classmethod
    @transaction.commit_on_success
    def create_instance(self, plan, environment):
        LOG.info("Provisioning new host on cloud portal with options %s %s..." % (plan, environment))

        api = self.auth(environment= environment)
        
        planattr = PlanAttr.objects.get(plan=plan)

        project_id = self.get_credentials(environment= environment).project

        request = { 'serviceofferingid': planattr.serviceofferingid, 
                          'templateid': planattr.templateid, 
                          'zoneid': planattr.zoneid,
                          'networkids': planattr.networkid,
                          'projectid': project_id,
                          #'userdata': b64encode(planattr.userdata),
                        }

        response = api.deployVirtualMachine('POST',request)
        
        LOG.info(" CloudStack response %s" % (response))

        try:
            if 'jobid' in response:
                LOG.info("VirtualMachine created!")
                request = {'projectid': '%s' % (project_id), 'id':'%s' % (response['id']) }
                
                host_attr = HostAttr()
                host_attr.vm_id = response['id']

                response = api.listVirtualMachines('GET',request)
                host = Host()
                host.hostname = response['virtualmachine'][0]['nic'][0]['ipaddress']
                host.cloud_portal_host = True
                host.save()
                LOG.info("Host created!")

                
                host_attr.vm_user = 'root'
                host_attr.vm_password = 'ChangeMe'
                host_attr.host = host
                host_attr.save()
                LOG.info("Host attrs custom attributes created!")

                instance = Instance()
                instance.address = host.hostname
                instance.port = 3306
                instance.is_active = True
                instance.is_arbiter = False
                instance.hostname = host
            
                databaseinfra = DatabaseInfra()
                databaseinfra.name = host_attr.vm_id
                databaseinfra.user  = 'root'
                databaseinfra.password = 'root'
                databaseinfra.engine = plan.engine_type.engines.all()[0]
                databaseinfra.plan = plan
                databaseinfra.environment = environment
                databaseinfra.capacity = 1
                databaseinfra.per_database_size_mbytes=0
                databaseinfra.endpoint = instance.address + ":%i" %(instance.port)
                databaseinfra.save()
                LOG.info("DatabaseInfra created!")
            else:
                return None

            instance.databaseinfra = databaseinfra
            instance.save()
            LOG.info("Instance created!")

            ssh_ok = self.check_ssh(host)
            
            if  ssh_ok:
                disk = StorageManager.create_disk(environment=environment, plan=plan, host=host)
                context = Context({"EXPORTPATH": disk['path']})
            
                template = Template(planattr.userdata)
                userdata = template.render(context)
            
                request = {'id': host_attr.vm_id, 'userdata': b64encode(userdata)}
                response = api.updateVirtualMachine('POST', request)            
                
                self.run_script(host, "/opt/dbaas/scripts/dbaas_userdata_script.sh")

                
                
                LOG.info("Host %s is ready!" % (host.hostname))
                return databaseinfra

        except Exception, e:
            LOG.warning("We could not create the VirtualMachine because %s" % e)

            if 'virtualmachine' in response:
                vm_id = response['virtualmachine'][0]['id']
                LOG.info("Destroying VirtualMachine %s on cloudstack." % (vm_id))
                api.destroyVirtualMachine('POST',{'id': "%s" % (vm_id)})
                LOG.info("VirtualMachine destroyed!")
                if disk:
                    LOG.info("Destroying storage...")
                    StorageManager.destroy_disk(environment= environment, plan= plan, host= host)
                    LOG.info("Storage destroyed!")
            else:
               LOG.warning("Something ocurred on cloudstack: %i, %s" % (response['errorcode'], response['errortext']))
            
            return None