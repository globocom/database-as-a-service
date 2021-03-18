class HostCommands(object):
    def __new__(cls, host):
        if host.is_ol6:
            return HostCommandOL6(host)
        if host.is_ol7:
            return HostCommandOL7(host)


class HostBaseCommands(object):

    def __init__(self, host):
        self.host = host
        self.infra = host.infra
        self.engine_name = host.infra.engine.name

    def exec_service_command(self, service_name, action, no_output=False):
        cmd = self.command_tmpl.format(
            service_name=service_name,
            action=action
        )
        if no_output:
            cmd += ' > /dev/null'

        return cmd

    def init_database_script(self, action, no_output=True):
        script = ''
        for instance in self.host.instances.all():
            script += "{};".format(self.database(
                action=action
            ))
            if instance.is_sentinel:
                script += "{};".format(self.secondary_service(
                    action=action,
                    no_output=True
                ))
        return script

    def secondary_service(self, action, no_output=True):
        return self.exec_service_command(
            service_name=self.SECONDARY_SERVICE_NAME_BY_ENGINE[
                self.engine_name
            ],
            action=action,
            no_output=no_output
        )

    def database(self, action, no_output=True):
        return self.exec_service_command(
            service_name=self.PRIMARY_SERVICE_NAME_BY_ENGINE[self.engine_name],
            action=action,
            no_output=no_output
        )

    def monit_script(self, action='start'):
        return """
            echo ""; echo $(date "+%Y-%m-%d %T") "- Monit"
            {}
        """.format(
            self.exec_service_command(
                service_name='monit',
                action=action
            )
        )

    def rsyslog(self, action, no_output=False):
        return self.exec_service_command(
            service_name='rsyslog',
            action=action,
            no_output=no_output
        )

    def telegraf(self, action, no_output=False):
        return self.exec_service_command(
            service_name='telegraf',
            action=action,
            no_output=no_output
        )

    def httpd(self, action, no_output=False):
        return self.exec_service_command(
            service_name='httpd',
            action=action,
            no_output=no_output
        )

    def heartbeat(self, action, no_output=False):
        return self.exec_service_command(
            service_name='pt-heartbeat',
            action=action,
            no_output=no_output
        )

    @property
    def command_tmpl(self):
        raise NotImplementedError()


class HostCommandOL6(HostBaseCommands):
    PRIMARY_SERVICE_NAME_BY_ENGINE = {
        'mongodb': 'mongodb',
        'redis': 'redis',
        'mysql': 'mysql',
        'mysql_percona': 'mysql'
    }
    SECONDARY_SERVICE_NAME_BY_ENGINE = {
        'mongodb': 'mongodb',
        'redis': 'sentinel',
        'mysql': '',
        'mysql_percona': ''
    }
    command_tmpl = '/etc/init.d/{service_name} {action}'


class HostCommandOL7(HostBaseCommands):
    PRIMARY_SERVICE_NAME_BY_ENGINE = {
        'mongodb': 'mongod',
        'redis': 'redis',
        'mysql': 'mysql',
        'mysql_percona': 'mysql'
    }
    PRIMARY_SERVICE_NAME_BY_ENGINE = {
        'mongodb': 'mongod',
        'redis': 'sentinel',
        'mysql': '',
        'mysql_percona': ''
    }
    command_tmpl = 'systemctl {action} {service_name}.service'
