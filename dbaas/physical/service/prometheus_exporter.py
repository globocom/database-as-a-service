import logging

from dbaas_credentials.models import CredentialType, Credential

LOG = logging.getLogger(__name__)


class Exporter(object):
    CAT_EXPORTER_CONFIG_COMMAND = None

    def __init__(self, path, user, password, project):
        self.exporter_path = path
        self.default_user = user
        self.default_password = password
        self.project = project

    def configure_exporter(self, host):
        self.change_password(host)
        self.change_address(host)

        raise Exception('Forcing for retry later')

    def change_password(self, host):
        LOG.info("Changing password for Host %s", host.hostname)
        return self._change_password(host, self.get_infra_credentials_from_host(host))

    def change_address(self, host, address=None):
        LOG.info("Changing address for Host %s", host.hostname)
        return self._change_address(host, address)

    def get_infra_credentials_from_host(self, host):
        LOG.info("Getting Credentials for Host %s", host.hostname)
        return self._get_infra_credentials(host.infra)

    def overwrite_config_file(self, host, new_config_string):
        LOG.info('Creating temp prometheus config file for Host %s', host.hostname)
        host.ssh.create_temp_file(file_name='new_config.service', content=new_config_string)

        LOG.info('Moving original prometheus config file to backup for Host %s', host.hostname)
        host.ssh.run_script('mv {} {}-backup'.format(self.exporter_path, self.exporter_path))

        LOG.info('Moving temp config file as main config file for Host %s', host.hostname)
        host.ssh.run_script('mv {} {}'.format('/tmp/new_config.service', self.exporter_path))

        return True

    def get_service_file(self, host):
        LOG.info('Getting service file for Host %s', host.hostname)
        return self._get_service_file(host)

    def _change_password(self, host, credentials):
        return

    def _change_address(self, host, address=None):
        return

    def _get_infra_credentials(self, infra):
        return

    def _get_service_file(self, host):
        service_config_file = host.ssh.run_script(self.CAT_EXPORTER_CONFIG_COMMAND)['stdout']
        return ''.join(service_config_file)


class RedisExporter(Exporter):
    def __init__(self, project):
        super(RedisExporter, self).__init__(
            path='/etc/systemd/system/redis_exporter.service',
            user=None,
            password=None,
            project=project
        )

        self.CAT_EXPORTER_CONFIG_COMMAND = 'cat {}'.format(self.exporter_path)

    def _get_infra_credentials(self, infra):
        return {'user': None, 'password': infra.password}

    def _change_password(self, host, credentials):
        config_string = self.get_service_file(host)

        part1 = config_string.split('--redis.password=')[0]
        part2 = config_string.split('--redis.password=')[1]
        part2 = '\n' + part2.split('\n', 1)[1]

        new_config_string = '{}--redis.password={}{}'.format(part1, credentials['password'], part2)
        self.overwrite_config_file(host, new_config_string)

    def _change_address(self, host, address=None):
        config_string = self.get_service_file(host)

        part1 = config_string.split('--redis.addr=')[0]
        part2 = config_string.split('--redis.addr=')[1]
        part2 = ' --' + part2.split('--', 1)[1]

        new_config_string = '{}--redis.addr=redis://{}:6379{}'.format(part1, host.address, part2)
        self.overwrite_config_file(host, new_config_string)
