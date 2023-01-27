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

    def change_password(self, host):
        LOG.info("Changing password for host %s", host.hostname)
        return self._change_password(host, self.get_infra_credentials_from_host(host))

    def change_address(self, host, address):
        LOG.info("Changing address for host %s", host.hostname)
        return self._change_address(host, address)

    def get_infra_credentials_from_host(self, host):
        LOG.info("Getting Credentials for Host %s", host.hostname)
        return self._get_infra_credentials(host.infra)

    def overwrite_config_file(self, host, new_config_string):
        LOG.info('Creating temp prometheus config file for host %s', host.hostname)
        replace_file = host.ssh.create_temp_file(file_name='new_config.service', content=new_config_string)
        LOG.debug(replace_file)
        LOG.info('Moving original prometheus config file to backup for host %s', host.hostname)
        move_original = host.ssh.run_script('mv {} {}-backup'.format(self.exporter_path, self.exporter_path))
        LOG.debug(move_original)
        LOG.info('Moving temp config file as main config file for host %s', host.hostname)
        move_tmp = host.ssh.run_script('mv {} {}'.format('/tmp/new_config.service', self.exporter_path))
        LOG.debug(move_tmp)
        return True

    def _change_password(self, host, credentials):
        return

    def _change_address(self, host, address):
        return

    def _get_infra_credentials(self, infra):
        return


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
        service_config_file = host.ssh.run_script(self.CAT_EXPORTER_CONFIG_COMMAND)['stdout']
        config_string = ''.join(service_config_file)

        part1 = config_string.split('--redis.password=')[0]
        part2 = config_string.split('--redis.password=')[1]
        part2 = '\n' + part2.split('\n', 1)[1]

        new_config_string = '{}--redis.password={}{}'.format(part1, credentials['password'], part2)
        self.overwrite_config_file(host, new_config_string)

        raise Exception('Forcing for retry later')

    def _change_address(self, host, address):
        return
