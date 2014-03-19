import hashlib, hmac, string, base64, urllib
import json, urllib
import logging
from django.conf import settings
from django.db import transaction
from physical import models
from drivers import factory_for
from time import sleep
from pexpect import pxssh


LOG = logging.getLogger(__name__)
class SignedApiCall(object):
    def __init__(self, api_url, apiKey, secret):
        self.api_url = api_url
        self.apiKey = apiKey
        self.secret = secret
 
    def request(self, args):
        args['apiKey'] = self.apiKey
 
        self.params = []
        self._sort_request(args)
        self._create_signature()
        self._build_post_request()
 
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
 
    def _build_post_request(self):
        self.query += '&signature=' + urllib.quote_plus(self.signature)
        self.value = self.api_url + '?' + self.query


class CloudStackClient(SignedApiCall):
    def __getattr__(self, name):
        def handlerFunction(*args, **kwargs):
            if kwargs:
                return self._make_request(name, kwargs)
            return self._make_request(name, args[0])
        return handlerFunction
 
    def _http_get(self, url):
        response = urllib.urlopen(url)
        return response.read()
 
    def _make_request(self, command, args):
        args['response'] = 'json'
        args['command'] = command
        self.request(args)
        data = self._http_get(self.value)
        key = command.lower() + "response"
        return json.loads(data)[key]

class CloudStackProvider(object):
    
    @classmethod
    @transaction.commit_on_success
    def create_instance(self, plan, environment, engine):
        LOG.debug("Provisioning new host on cloud portal...")

        api = CloudStackClient(settings.CLOUD_STACK_API_URL, settings.CLOUD_STACK_API_KEY, settings.CLOUD_STACK_API_SECRET)

        request = { 'serviceofferingid':'5a5a6fae-73db-44d6-a05e-822ed5bd0548', 
                          'templateid': '6e94d4d0-a1d6-405c-b226-e1ce6858c97d', 
                          'zoneid': 'c70c584b-4525-4399-9918-fff690489036',
                          'networkids': '250b249b-5eb0-476a-b892-c6a6ced45aad',
                          'projectid': '0be19820-1fe2-45ea-844e-77f17e16add5'
                        }

        response = api.deployVirtualMachine(request)
        print response
        host = models.Host()
        host.cp_id = response['id']

        if response['jobid']:

            LOG.debug("VirtualMachine created!")
            request = {'projectid': '0be19820-1fe2-45ea-844e-77f17e16add5', 'id':'%s' % (response['id']) }
            response = api.listVirtualMachines(request)
            
            host.hostname = response['virtualmachine'][0]['nic'][0]['ipaddress']
            host.cloud_portal_host = True
            host.save()
            LOG.debug("Host created!")
            
            instance = models.Instance()
            instance.address = host.hostname
            instance.port = 3306
            instance.is_active = True
            instance.is_arbiter = False
            instance.hostname = host
            
            databaseinfra = models.DatabaseInfra()
            databaseinfra.name = host.cp_id
            databaseinfra.user  = 'root'
            databaseinfra.password = 'root'
            databaseinfra.engine = engine
            databaseinfra.plan = plan
            databaseinfra.environment = environment
            databaseinfra.capacity = 1
            databaseinfra.per_database_size_mbytes=0
            databaseinfra.endpoint = instance.address + ":%i" %(instance.port)
            databaseinfra.save()
            LOG.debug("DatabaseInfra created!")


            instance.databaseinfra = databaseinfra
            instance.save()
            LOG.debug("Instance created!")

            LOG.debug("Waiting 2min to login on host....!")
            sleep(120)
            username = "root"
            password = "ChangeMe"
            conection = pxssh.pxssh()
            if conection.login(instance.address, username, password):
                LOG.debug("Logged in, returning databaseinfra!")
                return databaseinfra

            else:
                LOG.debug("Could not login on host!")
            

        else:
            raise('We could not create the VirtualMachine.     :(')
            LOG.debug("We could not create the VirtualMachine. :(")
     
    @classmethod
    @transaction.commit_on_success
    def destroy_instance(self, host):
        LOG.warning("Deleting the host on cloud portal...")
        api = CloudStackClient(settings.CLOUD_STACK_API_URL, settings.CLOUD_STACK_API_KEY, settings.CLOUD_STACK_API_SECRET)
        request = {  'projectid': '0be19820-1fe2-45ea-844e-77f17e16add5',
                           'id': '%s' % (host.cp_id)
                        }
        response = api.destroyVirtualMachine(request)
        
        if response['jobid']:
            LOG.warning("VirtualMachine destroyed!")

            instance = models.Instance.objects.get(hostname=host)
            databaseinfra = models.DatabaseInfra.objects.get(instances=instance)

            databaseinfra.delete()
            LOG.warning("DatabaseInfra destroyed!")
            instance.delete
            LOG.warning("Instance destroyed!")
            host.delete()
            LOG.warning("Host destroyed!")
        else:
            raise('We could not destroy the VirtualMachine.     :(')
            LOG.warning("We could not destroy the VirtualMachine. :(")