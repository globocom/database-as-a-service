# -*- coding: utf-8 -*-
from cloudstack_client import CloudStackClient
from django.conf import settings
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
    @transaction.commit_on_success
    def destroy_instance(self, database, *args, **kwargs):
        from logical.models import Credential, Database

        LOG.warning("Deleting the host on cloud portal...")

        if database.is_in_quarantine:
            host = database.databaseinfra.instances.all()[0].hostname
            host_attr = HostAttr.objects.filter(host= host)[0]
            super(Database, database).delete(*args, **kwargs)  # Call the "real" delete() method.
            
            LOG.info("Stop MySQL!")
            self.run_script(host, "/etc/init.d/mysql stop")
            
            LOG.info("Remove all data!")
            self.run_script(host, "rm -rf /data/*")
            
            plan = database.databaseinfra.plan
            LOG.info("Plan: %s" % plan)
            
            environment = database.databaseinfra.environment
            LOG.info("Environment: %s" % environment)
            
            LOG.info("Destroy storage!")
            StorageManager.destroy_disk(environment=environment, plan=plan, host=host)

            api = CloudStackClient(settings.CLOUD_STACK_API_URL, settings.CLOUD_STACK_API_KEY, settings.CLOUD_STACK_API_SECRET)
            request = {  'projectid': '%s' % (settings.CLOUD_STACK_PROJECT_ID),
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
        
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        client.connect(host.hostname, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        log_stdout = stdout.readlines()
        log_stderr = stderr.readlines()
        cod_ret_start = stdout.channel.recv_exit_status()
        LOG.info("Run Command Log stdout: %s" % log_stdout)
        LOG.info("Run Command Log stderr: %s" % log_stderr)
        return cod_ret_start
        

    @classmethod
    def check_ssh(self, host, retries=3, initial_wait=30, interval=30):
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
                LOG.info("Attempt number %i" % (x+1))
                LOG.info("Trying to login in on %s with user: %s and password: %s" % (host.hostname, host_attr.vm_user, host_attr.vm_password))
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

        api = CloudStackClient(settings.CLOUD_STACK_API_URL, settings.CLOUD_STACK_API_KEY, settings.CLOUD_STACK_API_SECRET)
        
        planattr = PlanAttr.objects.get(plan=plan)

        request = { 'serviceofferingid': planattr.serviceofferingid, 
                          'templateid': planattr.templateid, 
                          'zoneid': planattr.zoneid,
                          'networkids': planattr.networkid,
                          'projectid': settings.CLOUD_STACK_PROJECT_ID,
                          #'userdata': b64encode(planattr.userdata),
                        }

        response = api.deployVirtualMachine('POST',request)
        
        LOG.info(" CloudStack response %s" % (response))

        try:
            if response['jobid']:
                LOG.info("VirtualMachine created!")
                request = {'projectid': '%s' % (settings.CLOUD_STACK_PROJECT_ID), 'id':'%s' % (response['id']) }
                
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

            instance.databaseinfra = databaseinfra
            instance.save()
            LOG.info("Instance created!")

            ssh_ok = self.check_ssh(host)
            #from time import sleep
            #sleep(20)
            
            if  ssh_ok:
                disk = StorageManager.create_disk(environment=environment, plan=plan, host=host)
                c = Context({"EXPORTPATH": disk['path']})
            
                t = Template(planattr.userdata)
                userdata = t.render(c)
            
                request = {'id': host_attr.vm_id, 'userdata': b64encode(userdata)}
                response = api.updateVirtualMachine('POST', request)            
                
                ret_run_script = self.run_script(host, "/opt/dbaas/scripts/dbaas_userdata_script.sh")
                
                #LOG.info("Script Boot: %s" % ret_run_script)
                
                
                LOG.info("Host %s is ready!" % (host.hostname))
                return databaseinfra

        except (KeyError, LookupError):
            LOG.warning("We could not create the VirtualMachine because something ocurred on cloudstack: %i, %s" % (response['errorcode'], response['errortext']))
            return None