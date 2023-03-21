from requests import post, get
from dbaas_credentials.models import CredentialType


class IngressProvider(object):

    def __init__(self, instance, environment):
        self.instance = instance
        self._team = None
        self._vm_credential = None
        self._environment = environment

    @property
    def infra(self):
        return self.instance.databaseinfra

    @property
    def environment(self):
        return self._environment

    @property
    def host(self):
        return self.instance.hostname

    @property
    def engine(self):
        return self.infra.engine.full_name_for_host_provider

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                self.environment, CredentialType.VIP_PROVIDER
            )

        return self._credential

    @property
    def vm_credential(self):
        if not self._vm_credential:
            self._vm_credential = get_credentials_for(
                self.environment, CredentialType.VM,
            )

        return self._vm_credential

    @property
    def provider(self):
        return self.credential.project

    def _request(self, action, url, **kw):
        auth = (self.credential.user, self.credential.password,)
        kw.update(**{'auth': auth} if self.credential.user else {})
        return action(url, **kw)

    def create_ingress(self, infra, port, team_name, equipments,
                   vip_dns, database_name='', future_vip=False):
    ##
        url = "{}/{}/{}/vip/new".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "group": infra.name,
            "port": port,
            "team_name": team_name,
            "equipments": equipments,
            "vip_dns": vip_dns,
            "database_name": database_name
        }
        ## faz a request
        response = self._request(post, url, json=data, timeout=600)

        if response.status_code not in [200, 201]:
            raise VipProviderCreateVIPException(response.content, response)

        if response.status_code == 200:
            return None

        content = response.json()

        try:
            original_vip = Vip.objects.get(infra=infra)
        except Vip.DoesNotExist:
            original_vip = None
        vip = Vip()
        vip.identifier = content["identifier"]
        vip.infra = infra
        vip.vip_ip = content["ip"]
        if original_vip:
            vip.original_vip = original_vip
        vip.save()

        return vip


class IngressProviderStep(BaseInstanceStep):

    def __init__(self, instance=None):
        super(IngressProviderStep, self).__init__(instance)
        self.credentials = None
        self._provider = None

    @property
    def provider(self):
        if not self._provider:
            self._provider = Provider(self.instance, self.environment)
        return self._provider

    @property
    def vm_properties(self):
        if not (hasattr(self, '_vm_properties') and self._vm_properties):
            self._vm_properties = self.host_prov_client.get_vm_by_host(
                self.host)
        return self._vm_properties

    @property
    def equipments(self):
        equipments = []
        ## TODO CHECK
        for instance in self.infra.instances.filter(future_instance=None):
            host = instance.hostname
            if host.future_host:
                host = host.future_host
            vm_info = self.host_prov_client.get_vm_by_host(host)
            equipment = {
                'host_address': host.address,
                'port': instance.port,
                'identifier': vm_info.identifier,
                'zone': vm_info.zone,
                'group': vm_info.group,
                'name': vm_info.name
            }
            equipments.append(equipment)
        return equipments

    @property
    def team(self):
        if self.has_database:
            return self.database.team.name
        elif self.create:
            return self.create.team.name
        elif (self.step_manager
              and hasattr(self.step_manager, 'origin_database')):
            return self.step_manager.origin_database.team.name

    @property
    def current_vip(self):
        vip = Vip.objects.filter(infra=self.infra)
        if vip.exists():
            return vip.last()

        return None

    @property
    def current_instance_group(self):
        if not self.current_vip:
            return None

        return VipInstanceGroup.objects.filter(vip=self.current_vip)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class AllocateProvider(VipProviderStep):

    def __init__(self, instance, environment):
        self.url = "pudim.com.br"
        self.instance = instance
        self._vm_credential = None
        self._environment = environment

    def __unicode__(self):
        return "Allocating Provider on k8s cluster..."

    def do(self):
        if not self.is_valid:
            return

        data = {
            "team": "team A",
            "bank_port": 27017,
            "bank_address": ["10.96.166.229"],
            "bank_type": "mongodb",
            "bank_name": "test_dani_dbaas_dev",
            "bank_service_account": "testdanidb167821582559@gglobo-dbaaslab-dev-qa.iam.gserviceaccount.com"
        }
        ## faz a request
        response = self.IngProvUtils._request(post, self.url, json=data, timeout=6000)

        dns = add_dns_record(
            self.infra, self.infra.name,
            self.vip_ip, FOXHA, is_database=False)

        if dns is None:
            return

        self.infra.endpoint_dns = "{}:{}".format(dns, 3306)
        self.infra.save()

    def undo(self):
        pass


class CheckProviderIp(object):

    def __init__(self, instance, environment):
        self.url = "pudim.com.br"
        self.instance = instance
        self._vm_credential = None
        self._environment = environment

    def __unicode__(self):
        return "Retrieving Provider IP..."

    def do(self):
        if not self.is_valid:
            return

        data = {
            "team": "team A",
            "bank_port": 27017,
            "bank_address": ["10.96.166.229"],
            "bank_type": "mongodb",
            "bank_name": "test_dani_dbaas_dev",
            "bank_service_account": "testdanidb167821582559@gglobo-dbaaslab-dev-qa.iam.gserviceaccount.com"
        }
        ## faz a request
        response = self._request(post, url, json=data, timeout=6000)

        dns = add_dns_record(
            self.infra, self.infra.name,
            self.vip_ip, FOXHA, is_database=False)

        if dns is None:
            return

        self.infra.endpoint_dns = "{}:{}".format(dns, 3306)
        self.infra.save()

    def undo(self):
        pass
