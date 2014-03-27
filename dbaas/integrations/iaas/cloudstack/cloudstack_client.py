import hashlib, hmac, string, base64, urllib
import json, urllib
import logging
from django.conf import settings
from django.db import transaction
from physical.models import DatabaseInfra, Instance, Host
from drivers import factory_for
from .models import PlanAttr, HostAttr
import logging
from base64 import b64encode
from ..base import BaseProvider


LOG = logging.getLogger(__name__)

class SignedApiCall(object):
    def __init__(self, api_url, apiKey, secret):
        self.api_url = api_url
        self.apiKey = apiKey
        self.secret = secret
 
    def request(self, args, action):
        args['apiKey'] = self.apiKey
 
        self.params = []
        self._sort_request(args)
        self._create_signature()
        self._build_post_request(action)
 
    def _sort_request(self, args):
        keys = sorted(args.keys())
 
        for key in keys:
            self.params.append(key + '=' + urllib.quote_plus(args[key]))
 
    def _create_signature(self):
        self.query = '&'.join(self.params)
        digest = hmac.new(
            self.secret,
            msg=self.query.lower(),
            digestmod=hashlib.sha1).digest()
 
        self.signature = base64.b64encode(digest)
 
    def _build_post_request(self, action):
        self.query += '&signature=' + urllib.quote_plus(self.signature)
        self.value = self.api_url
        if action == 'GET':
            self.value += '?' + self.query


class CloudStackClient(SignedApiCall):
    def __getattr__(self, name):
        def handlerFunction(*args, **kwargs):
            action = args[0] or 'GET'
            if kwargs:
                return self._make_request(name, kwargs)
            return self._make_request(name, args[1], action)
        return handlerFunction
 
    def _http_get(self, url):
        response = urllib.urlopen(url)
        return response.read()

    def _http_post(self, url, data):
        response = urllib.urlopen(url,data)
        return response.read()
 
    def _make_request(self, command, args, action):
        args['response'] = 'json'
        args['command'] = command
        self.request(args,action)
        if action == 'GET':
            data = self._http_get(self.value)
        else:
            data = self._http_post(self.value, self.query)
        # The response is of the format {commandresponse: actual-data}
        key = command.lower() + "response"
        return json.loads(data)[key]

class CloudStackProvider(BaseProvider):
        
    @classmethod
    @transaction.commit_on_success
    def destroy_instance(self, host):
        LOG.warning("Deleting the host on cloud portal...")
        api = CloudStackClient(settings.CLOUD_STACK_API_URL, settings.CLOUD_STACK_API_KEY, settings.CLOUD_STACK_API_SECRET)
        request = {  'projectid': '0be19820-1fe2-45ea-844e-77f17e16add5',
                           'id': '%s' % (host.cp_id)
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
                host.host_attr.delete()
                LOG.info("Host custom cloudstack attrs destroyed!")
                host.delete()
                LOG.info("Host destroyed!")
        except (KeyError, LookupError):
            LOG.warning("We could not destroy the VirtualMachine. :(")


    @classmethod
    def check_ssh(self, host, retries=3, initial_wait=30, interval=30):
        from time import sleep
        import paramiko
        import socket

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
                          'userdata': b64encode(planattr.userdata),
                        }

        response = api.deployVirtualMachine('POST',request)
        
        LOG.info(" CloudStack response %s" % (response))

        try:
            if response['jobid']:
                LOG.info("VirtualMachine created!")
                request = {'projectid': '%s' % (settings.CLOUD_STACK_PROJECT_ID), 'id':'%s' % (response['id']) }
                response = api.listVirtualMachines('GET',request)
                
                host = Host()
                host.cp_id = response['id']
                host.hostname = response['virtualmachine'][0]['nic'][0]['ipaddress']
                host.cloud_portal_host = True
                host.save()
                LOG.info("Host created!")

                host_attr = HostAttr()
                host_attr.vm_id = host.cp_id
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
                databaseinfra.name = host.cp_id
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
                
            if  ssh_ok:
                LOG.info("Host %s is ready!" % (host.hostname))
                return databaseinfra

        except (KeyError, LookupError):
            LOG.warning("We could not create the VirtualMachine because something ocurred on cloudstack: %i, %s" % (response['errorcode'], response['errortext']))
            return None
