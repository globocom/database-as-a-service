# encoding: utf-8

import httplib
import urlparse
from django.utils import simplejson as json
import logging
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType

LOG = logging.getLogger(__name__)

GET = 'GET'
POST = 'POST'
DELETE = 'DELETE'
PUT = 'PUT'
FAKE = False  # False habilita, True desliga


class DNSAPI(object):

    def __init__(self, environment):
        credential = Credential.get_credentials(environment= environment, integration= CredentialType.objects.get(type= CredentialType.DNSAPI))
        
        #self.base_url = 'http://globodns.dev.globoi.com/users/sign_in'
        self.base_url = credential.endpoint
        self.username = credential.user
        self.password = credential.password
        self.token = None

    def __request(self, method, path, data=None, use_token=True, retry=True):
        complete_url = self.base_url + path
        url = urlparse.urlparse(complete_url)
        url_path = url.path

        # obtém o token logo no inicio da requisição, para evitar que o log fique com as mensagens
        # de requisição entrelaças (iniciando uma e parando para fazer outra)
        headers = {'Content-type': 'application/json'}
        if use_token:
            data = data or {}
            data['auth_token'] = self.__request_token()

        data_string = json.dumps(data, indent=2) if data else None
        LOG.debug(u'Requisição %s %s', method, complete_url)

        if url.scheme == 'https':
            http = httplib.HTTPSConnection(url.hostname, url.port or 443)
        else:
            http = httplib.HTTPConnection(url.hostname, url.port or 80)

        http.request(method, url_path, data_string, headers)
        response = http.getresponse()
        response_string = response.read()
        LOG.debug(u'Response: %d %s\nContent-type: %s\n%s', response.status,
                  response.reason, response.getheader('Content-type'), response_string)

        if response.status == 422:
            raise DNSMissingParameter(path)

        if response.status == 404:
            raise DNSNotFound(path)

        # se o token expirou, refaz a requisição (se não já for a segunda chamada)
        if response.status == 401 and retry:
            LOG.info(u'Chamada DNSAPI com token inválido... gerando novo token e retentando...')
            self.__request_token(force=True)
            return self.__request(method, path, data, retry=False)

        if response.status == 204:  # no content
            return None

        if not (response.status in [200, 201]):
            LOG.error(u'Response: %d %s\nContent-type: %s\n%s', response.status,
                      response.reason, response.getheader('Content-type'), response_string)
            raise DNSUnknownError(path, response.status)

        if response.getheader('Content-type', 'application/json').startswith('application/json'):
            return json.loads(response_string)

        return response_string

    def __request_token(self, force=False):
        if not self.token or force:
            auth = self.__request(POST, '/users/sign_in.json', {'user': {
                                  'email': self.username, 'password': self.password}}, use_token=False, retry=False)
            self.token = auth['authentication_token']
        return self.token

    def get_domain_id_by_name(self, domain='globoi.com'):
        """ Recupera o id do dominio """
        id = self.__request(GET, '/domains.json', data={'query': domain})

        if id:
            return id[0]['domain'].get('id')
        else:
            return None

    def translate_ip_to_reverse_domain(self, ip):
        if FAKE:
            return {}
        # converte o ip para o formato padrao de domain reverso (ex: 1.2.3.4 => 4.3.2)
        return '.'.join(ip.split('.')[2::-1]) + '.in-addr.arpa'

    def get_reverse_domain_id_by_name(self, reverse_domain):
        if FAKE:
            return {}
        id_rev_domain = self.__request(GET, '/domains.json?', data={'reverse': 'true', 'query': reverse_domain})
        if id_rev_domain:
            return id_rev_domain[0]['domain'].get('id')
        else:
            return self.create_reverse_domain(reverse_domain)['domain'].get('id')

    def get_template_id_by_name(self, template_name_to_match='Template geral (usar por default)'):
        LOG.info(u'Buscando id do template name: %s', template_name_to_match)
        my_templates = self.__request(GET, '/domain_templates.json')
        for domain_template in my_templates:
            for e_template in domain_template:
                if domain_template[e_template]['name'] == template_name_to_match:
                    return domain_template[e_template]['id']
        raise DNSTemplateNameNotFound(template_name_to_match)

    def create_reverse_domain(self, name):
        LOG.info(u'Criando o dominio reverso %s', name)
        template_id = self.get_template_id_by_name()
        return self.__request(POST, '/domains.json', {'domain': {'name': name, 'domain_template_id': template_id, 'authority_type': 'M', 'reverse': 'true'}})

    def generate_reverse_host_name(self, name, domain):
        return name + '.' + domain + '.'

    def create_reverse_record(self, ip, name, record_type="PTR"):
        if FAKE:
            return {}
        id_domain = self.get_reverse_domain_id_by_name(self.translate_ip_to_reverse_domain(ip))
        reverse_name = self.generate_reverse_host_name(name, 'globoi.com')  # hard cooded, precisa melhorar.
        record_exist = self.get_record_by_name(self.get_last_oct(ip), record_type='PTR', domain_id=id_domain)
        if record_exist:
            self.delete_record(record_exist, reverso=True)
        record = self.__request(POST, '/domains/%d/records.json' % id_domain,
                                {"record": {"content": reverse_name, "type": record_type, "name": ip.split('.')[-1]}})
        record = record['record']
        LOG.info(u'Cadastrado o reverso: %s', record)
        return record

    def get_record(self, record_id):
        if FAKE:
            return {}
        record = self.__request(GET, '/records/%d.json' % record_id)
        return record.values()[0]

    def get_record_by_name(self, name, record_type='A', domain_id=None):
        """ Busca um registro no dominio através do nome """
        if domain_id is not None:
            record = self.__request(GET, '/domains/' + str(domain_id) + '/records.json', data={'query': name})

        if record:
            return record[0][str(record_type.lower())].get('id')
        else:
            return None

    def create_record(self, name, content, record_type="A", domain_id=None):
        if FAKE:
            return {}
        if domain_id is not None:
            id_record = self.get_record_by_name(name, domain_id=domain_id)
        if id_record:
            LOG.warning(u'O record %s já existia e sera substituido', name)
            self.delete_record(id_record)

        record = self.__request(POST, '/domains/%d/records.json' % domain_id,
                                {"record": {"name": name, "type": record_type, "content": content}})
        self.create_reverse_record(content, name)
        record = record['record']
        LOG.info(u'Cadastrado a entrada: %s', record)
        return record

    def get_last_oct(self, ip):
        oct = ip.split('.')
        oct = oct[-1]
        return oct

    def delete_record(self, record_id, reverso=False):
        if FAKE:
            return None
        LOG.info(u'O record %s foi removido', record_id)
        if reverso:
            self.__request(DELETE, '/records/%d.json' % record_id, {"reverse": "true"})
        else:
            self.__request(DELETE, '/records/%d.json' % record_id)
        return None

    def delete_record_by_name(self, host_name, ip, domain='globoi.com'):
        '''Dado o hostname e dominio, removo a entrada no DNS e seu reverso'''
        if FAKE:
            return None
        default_domain_id = self.domain_id_discover(domain)
        reverse_domain_id = self.get_reverse_domain_id_by_name(self.translate_ip_to_reverse_domain(ip))
        record_id = self.get_record_by_name(host_name, domain_id=default_domain_id)
        reverse_record_id = self.get_record_by_name(self.get_last_oct(ip), record_type='PTR', domain_id=reverse_domain_id)
        if record_id:
            self.delete_record(record_id)
            LOG.info(u'O record %s (id: %s) foi removido', host_name, record_id)
        else:
            LOG.warning(u'O record %s.%s não foi encontrado.', host_name, record_id)
        if reverse_record_id:
            self.delete_record(reverse_record_id, reverso=True)
            LOG.info(u'O record %s (id: %s) foi removido', ip, reverse_record_id)
        else:
            LOG.warning(u'O record %s.%s não foi encontrado.', ip, reverse_record_id)
        return None

    def update_record(self, record_id, name, content, record_type="A"):
        if FAKE:
            return {}
        self.__request(PUT, '/records/%d.json' % record_id,
                       {"record": {"name": name, "type": record_type, "content": content}})

    def domain_id_discover(self, name):
        """ Recebe uma url e retorna o id do dominio relativo
        a ser cadastrada.
        """
        size = len(name.split('.'))
        for register in range(0, (size - 1)):
            domain = '.'.join(name.split('.')[register:])
            lookup_id = self.get_domain_id_by_name(domain=domain)
            if lookup_id:
                return lookup_id
                break

    def export(self, now=True, all=False):
        if FAKE:
            return None
        params = {}
        if all:
            params['all'] = 'true'
            output = self.__request(POST, '/bind9/export.json', params)
        if now:
            params['now'] = 'true'
            output = self.__request(POST, '/bind9/export.json', params)
        if not now:
            output = self.__request(POST, '/bind9/schedule_export.json')
        LOG.info('Resultado da chamada de exportação do DNS: %s', output)
        return output


class DNSNotFound(Exception):

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'DNSNotFound(%s)' % (repr(self.path),)


class DNSMissingParameter(Exception):

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'DNSMissingParameter(%s)' % (repr(self.path),)


class DNSUnknownError(Exception):

    def __init__(self, path, status):
        self.path = path
        self.status = status

    def __str__(self):
        return 'DNSUnknownError(%s, http=%d)' % (repr(self.path), self.status)

class DNSTemplateNameNotFound(Exception):
    pass
