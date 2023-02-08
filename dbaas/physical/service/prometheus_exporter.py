import datetime
import logging

from dbaas_credentials.models import CredentialType
from dbaas_credentials.credential import Credential

LOG = logging.getLogger(__name__)


class Exporter(object):
    def __init__(self, path, user, password, project, service_name):
        self.exporter_path = path
        self.default_user = user
        self.default_password = password
        self.project = project
        self.service_name = service_name

    def configure_host_exporter(self, host):
        self.change_credentials(host)
        self.change_address(host)
        self.restart_service(host)

    def change_credentials(self, host):
        # Changes only the credentials for the exporter (user and password) and doesn't touch the remaining configs
        LOG.info("Changing prometheus exporter password for Host %s", host.hostname)
        return self._change_credentials(host, self.get_infra_credentials_from_host(host))

    def change_address(self, host, address=None):
        # Changes only the address for the exporter (localhost, 0.0.0.0) and doesn't touch the remaining configs
        LOG.info("Changing prometheus exporter address for Host %s", host.hostname)
        return self._change_address(host, address)

    def get_infra_credentials_from_host(self, host):
        LOG.info("Getting Credentials for Host %s", host.hostname)
        return self._get_infra_credentials(host.infra)

    def overwrite_config_file(self, host, new_config_string):
        LOG.info('Overwriting prometheus config file for Host %s', host.hostname)
        return self._overwrite_config(host, new_config_string)

    def restart_service(self, host):
        LOG.info('Restarting prometheus exporter service for Host %s', host.hostname)
        return self._restart_service(host)

    @property
    def cat_exporter_config_command(self):
        return 'cat {}'.format(self.exporter_path)

    def get_service_file(self, host):
        LOG.info('Getting prometheus exporter service file for Host %s', host.hostname)
        return self._get_service_file(host)

    def _change_credentials(self, host, credentials):
        return

    def _change_address(self, host, address=None):
        return

    def _get_infra_credentials(self, infra):
        return

    def _get_service_file(self, host):
        service_config_file = host.ssh.run_script(self.cat_exporter_config_command)['stdout']
        return ''.join(service_config_file)

    def _restart_service(self, host):
        host.ssh.run_script('systemctl daemon-reload & systemctl restart {}'.format(self.service_name))

    def _overwrite_config(self, host, new_config_string):
        LOG.info('Creating temp prometheus config file for Host %s', host.hostname)
        host.ssh.create_temp_file(file_name='new_config.service', content=new_config_string)

        LOG.info('Moving original prometheus config file to backup for Host %s', host.hostname)
        host.ssh.run_script('mv {} {}-backup-{}'.format(
            self.exporter_path, self.exporter_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))

        LOG.info('Moving prometheus temp config file as main config file for Host %s', host.hostname)
        host.ssh.run_script('mv {} {}'.format('/tmp/new_config.service', self.exporter_path))

        return True


class RedisExporter(Exporter):
    """
    Config file example:

    [Unit]
    Description=Redis Exporter
    After=network.target

    [Service]
    Type=simple
    ExecStart=/usr/local/bin/prometheus/redis_exporter --debug --redis.addr=redis://0.0.0.0:6379 --redis.password=1234

    [Install]
    WantedBy=multi-user.target
    """
    def __init__(self, project):
        super(RedisExporter, self).__init__(
            path='/etc/systemd/system/redis_exporter.service',
            user=None,
            password=None,
            project=project,
            service_name='redis_exporter'
        )

    def _get_infra_credentials(self, infra):
        return {'user': None, 'password': infra.password}

    def _change_credentials(self, host, credentials):
        config_string = self.get_service_file(host)

        password_begin_in_config = config_string.split('--redis.password=')[1]
        original_password = password_begin_in_config.split('\n', 1)[0]
        if original_password != "":
            new_config = config_string.replace(original_password, credentials['password'])
        else:
            new_config = config_string.replace('--redis.password=', '--redis.password=' + credentials['password'])
        self.overwrite_config_file(host, new_config)

    def _change_address(self, host, address=None):
        config_string = self.get_service_file(host)

        address_begin_in_config = config_string.split('--redis.addr=')[1]
        original_address = address_begin_in_config.split('--', 1)[0]
        new_config_string = config_string.replace(original_address, 'redis://{}:6379 '.format(host.address))
        self.overwrite_config_file(host, new_config_string)


class MongoDBExporter(Exporter):
    """
    Config file example:

    [Unit]
    Description=Mongodb Exporter
    After=network.target

    [Service]
    Type=simple
    ExecStart=/usr/local/bin/prometheus/mongodb_exporter --mongodb.uri=mongodb://admin:pass@0.0.0.0:27017/admin

    [Install]
    WantedBy=multi-user.target
    """
    def __init__(self, project):
        credential = Credential.get_credentials(
            environment=project,
            integration=CredentialType.objects.get(type=CredentialType.MONGODB)
        )

        super(MongoDBExporter, self).__init__(
            path='/etc/systemd/system/mongodb_exporter.service',
            user=credential.user,
            password=credential.password,
            project=project,
            service_name='mongodb_exporter'
        )

    def _get_infra_credentials(self, infra):
        return {'user': self.default_user, 'password': self.default_password}

    def _change_address(self, host, address=None):
        config_string = self.get_service_file(host)

        address_begin_in_config = config_string.split('@')[1]
        original_address = address_begin_in_config.split('--', 1)[0]

        LOG.debug('Original address: %s', original_address)

        new_config_string = config_string.replace(original_address, '{}:27017/admin '.format(host.address))
        self.overwrite_config_file(host, new_config_string)

    def _change_credentials(self, host, credentials):
        config_string = self.get_service_file(host)

        credentials_begin_in_config = config_string.split('mongodb://')[1]
        original_credentials = credentials_begin_in_config.split('@', 1)[0]

        new_config_string = config_string.replace(
            original_credentials, '{}:{}'.format(credentials['user'], credentials['password']))
        self.overwrite_config_file(host, new_config_string)


class MySQLExporter(Exporter):
    """
    Config file example:

    [client]
    user=root
    password=123456
    """
    def __init__(self, project):
        credential = Credential.get_credentials(
            environment=project,
            integration=CredentialType.objects.get(type=CredentialType.MYSQL)
        )

        super(MySQLExporter, self).__init__(
            path='/etc/.dbconf.cnf',
            user=credential.user,
            password=credential.password,
            project=project,
            service_name='mysql_exporter'
        )

    def _get_infra_credentials(self, infra):
        return {'user': self.default_user, 'password': self.default_password}

    def _change_credentials(self, host, credentials):
        config_string = self.get_service_file(host)

        user_begin_in_config = config_string.split('user=')[1]
        original_user = user_begin_in_config.split('\n', 1)[0]

        new_config_string = config_string.replace('user={}'.format(original_user),
                                                  'user={}'.format(credentials['user']))

        original_password = new_config_string.split('password=')[1]
        new_config_string = new_config_string.replace('password={}'.format(original_password),
                                                      'password={}'.format(credentials['password']))

        self.overwrite_config_file(host, new_config_string)
