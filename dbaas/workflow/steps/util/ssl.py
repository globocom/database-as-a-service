from util import exec_remote_command_host
from base import BaseInstanceStep
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
import json
import logging

LOG = logging.getLogger(__name__)


class SSLFiles(object):

    @property
    def ssl_path(self):
        return '/data/ssl'

    def conf_file(self, basename):
        return basename + '.conf'

    def csr_file(self, basename):
        return basename + '-cert.csr'

    def key_file(self, basename):
        return basename + "-key.pem "

    def json_file(self, basename):
        return basename + '-cert.json'

    def ca_file(self, basename):
        return basename + "-ca.pem "

    def cert_file(self, basename):
        return basename + "-cert.pem "


class SSL(BaseInstanceStep):

    def __init__(self, instance):
        super(SSL, self).__init__(instance)
        self.credential = get_credentials_for(
            self.environment, CredentialType.PKI)
        self.certificate_allowed = self.credential.get_parameter_by_name(
            'certificate_allowed')
        self.master_ssl_ca = self.credential.get_parameter_by_name(
            'master_ssl_ca')
        self.certificate_type = self.credential.get_parameter_by_name(
            'certificate_type')
        self.ssl_files = SSLFiles()

    @property
    def ssl_path(self):
        return self.ssl_files.ssl_path

    @property
    def ssl_file_basename(self):
        raise NotImplementedError

    @property
    def conf_file(self):
        return self.ssl_files.conf_file(self.ssl_file_basename)

    @property
    def csr_file(self):
        return self.ssl_files.csr_file(self.ssl_file_basename)

    @property
    def key_file(self):
        return self.ssl_files.key_file(self.ssl_file_basename)

    @property
    def json_file(self):
        return self.ssl_files.json_file(self.ssl_file_basename)

    @property
    def ca_file(self):
        return self.ssl_files.ca_file(self.ssl_file_basename)

    @property
    def cert_file(self):
        return self.ssl_files.cert_file(self.ssl_file_basename)

    @property
    def conf_file_path(self):
        return self.ssl_path + '/' + self.conf_file

    @property
    def csr_file_path(self):
        return self.ssl_path + '/' + self.csr_file

    @property
    def key_file_path(self):
        return self.ssl_path + '/' + self.key_file

    @property
    def json_file_path(self):
        return self.ssl_path + '/' + self.json_file

    @property
    def ca_file_path(self):
        return self.ssl_path + '/' + self.ca_file

    @property
    def cert_file_path(self):
        return self.ssl_path + '/' + self.cert_file

    @property
    def ssl_dns(self):
        raise NotImplementedError

    @property
    def is_valid(self):
        return (
            str(self.certificate_allowed).lower() == 'true' and
            self.plan.replication_topology.can_setup_ssl
            )


    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    def exec_script(self, script):
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(str(output))
        LOG.info("output: {}".format(output))
        return output


class UpdateOpenSSlLib(SSL):

    def __unicode__(self):
        return "Updating OpenSSL Lib..."

    def do(self):
        if not self.is_valid: return
        script = "yum update -y openssl"
        self.exec_script(script)


class CreateSSLFolder(SSL):

    def __unicode__(self):
        return "Creating SSL Folder..."

    def do(self):
        if not self.is_valid: return
        script = "mkdir -p {}".format(self.ssl_path)
        self.exec_script(script)

    def undo(self):
        if not self.is_valid: return
        script = "rm -rf {}".format(self.ssl_path)
        self.exec_script(script)


class InstanceSSLBaseName(SSL):
    @property
    def ssl_file_basename(self):
        return self.instance.hostname.hostname.split('.')[0]


class InfraSSLBaseName(SSL):
    @property
    def ssl_file_basename(self):
        return self.infra.name


class InstanceSSLDNS(SSL):
    @property
    def ssl_dns(self):
        if self.certificate_type == 'IP':
            return self.instance.address
        else:
            return self.instance.dns


class InstanceSSLDNSIp(SSL):
    @property
    def ssl_dns(self):
        return self.instance.address


class InfraSSLDNS(SSL):
    @property
    def ssl_dns(self):
        if self.certificate_type == 'IP':
            return self.infra.endpoint.split(':')[0]
        else:
            return self.infra.endpoint_dns.split(':')[0]


class CreateSSLConfigFile(SSL):
    def __unicode__(self):
        return "Creating SSL Config File..."

    def create_ssl_config_file(self):

        script = """(cat <<EOF_SSL
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no
[req_distinguished_name]
C = BR
ST = RJ
L = Rio de Janeiro
O = Globo Comunicacao e Participacoes SA
OU = Data Center-Globo.com
emailAddress = dns-tech\@corp.globo.com
CN = {dns}
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = {dns}
EOF_SSL
) > {file_path}""".format(dns=self.ssl_dns, file_path=self.conf_file_path)

        self.exec_script(script)

    def do(self):
        if not self.is_valid: return
        self.create_ssl_config_file()


class CreateSSLConfForInstanceDNS(CreateSSLConfigFile,
                                  InstanceSSLBaseName,
                                  InstanceSSLDNS):
    pass


class CreateSSLConfForInstanceIP(CreateSSLConfigFile,
                                 InstanceSSLBaseName,
                                 InstanceSSLDNSIp):
    pass


class CreateSSLConfForInfraEndPoint(CreateSSLConfigFile,
                                    InfraSSLBaseName,
                                    InfraSSLDNS):
    pass


class RequestSSL(SSL):

    def __unicode__(self):
        return "Requesting SSL..."

    def request_ssl_certificate(self):
        script = "cd {ssl_path}\n"
        script += "openssl req -new -out {csr} -newkey rsa:2048 "
        script += "-nodes -sha256 -keyout {key} -config {conf}"

        script = script.format(
            ssl_path=self.ssl_path, csr=self.csr_file,
            key=self.key_file, conf=self.conf_file)

        self.exec_script(script)

    def do(self):
        if not self.is_valid: return
        self.request_ssl_certificate()


class RequestSSLForInstance(RequestSSL, InstanceSSLBaseName):
    pass


class RequestSSLForInfra(RequestSSL, InfraSSLBaseName):
    pass


class CreateJsonRequestFile(SSL):

    def __unicode__(self):
        return "Creating JSON SSL File..."

    def read_csr_file(self):
        script = "cat {}".format(self.csr_file_path)
        output = self.exec_script(script)
        csr_content = ''
        for line in output['stdout']:
            csr_content += line
        return csr_content.rstrip('\n').replace('\n', '\\n')

    def create_json_request(self, csr_content):

        script = """(cat <<EOF_SSL
{{"certificate":
{{"ttl": "8760",
"csr": "{csr_content}"}}
}}
EOF_SSL
) > {file_path}"""

        script = script.format(
            csr_content=csr_content, file_path=self.json_file_path)

        self.exec_script(script)

    def do(self):
        if not self.is_valid: return
        csr_content = self.read_csr_file()
        self.create_json_request(csr_content)



class CreateJsonRequestFileInstance(CreateJsonRequestFile,
                                    InstanceSSLBaseName):
    pass


class CreateJsonRequestFileInfra(CreateJsonRequestFile, InfraSSLBaseName):
    pass


class CreateCertificate(SSL):

    def __unicode__(self):
        return "Creating certificate..."

    def create_certificate_script(self):
        script = 'curl -d @{json} -H "X-Pki: 42" -H "Content-type: '
        script += 'application/json" {endpoint}'
        script = script.format(
            json=self.json_file_path, endpoint=self.credential.endpoint)
        return script

    def save_certificate_file(self, certificate, filepath):
        script = "echo '{}' > {}".format(certificate, filepath)
        self.exec_script(script)

    def do(self):
        if not self.is_valid: return
        script = self.create_certificate_script()
        output = self.exec_script(script)
        certificates = json.loads(output['stdout'][0])

        ca_chain = certificates['ca_chain'][0]
        self.save_certificate_file(ca_chain, self.ca_file_path)

        certificate = certificates['certificate']
        self.save_certificate_file(certificate, self.cert_file_path)


class CreateCertificateInstance(CreateCertificate, InstanceSSLBaseName):
    pass


class CreateCertificateInfra(CreateCertificate, InfraSSLBaseName):
    pass


class SetSSLFilesAccessMySQL(SSL):
    def __unicode__(self):
        return "Setting SSL Files Access..."

    def sll_file_access_script(self):
        script = "cd {}\n".format(self.ssl_path)
        script += "chown mysql:mysql *\n"
        script += "chown mysql:mysql .\n"
        script += "chmod 400 *key*.pem\n"
        script += "chmod 444 *cert*.pem\n"
        script += "chmod 755 ."
        self.exec_script(script)

    def do(self):
        if not self.is_valid: return
        self.sll_file_access_script()


class SetInfraConfiguredSSL(SSL):
    def __unicode__(self):
        return "Setting infra as SSL configured..."

    def do(self):
        if not self.is_valid: return
        infra = self.infra
        infra.ssl_configured = True
        infra.save()

    def undo(self):
        if not self.is_valid: return
        infra = self.infra
        infra.ssl_configured = False
        infra.save()


class SetReplicationUserRequireSSL(SSL):
    def __unicode__(self):
        return "Setting replication user to require SSL..."

    @property
    def is_valid(self):
        if not self.plan.is_ha:
            return False
        return super(SetReplicationUserRequireSSL, self).is_valid

    def do(self):
        if not self.is_valid: return

        driver = self.infra.get_driver()
        driver.set_replication_require_ssl(
            instance=self.instance, ca_path=self.master_ssl_ca)
        driver.set_replication_user_require_ssl()

    def undo(self):
        if not self.is_valid: return

        driver = self.infra.get_driver()
        driver.set_replication_user_not_require_ssl()
        driver.set_replication_not_require_ssl(instance=self.instance)

