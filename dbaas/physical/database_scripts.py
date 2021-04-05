import re

from django.template import Context, Template


class ArgsNotAllowed(Exception):
    pass


def update_instance_variables(function):
    def wrapper(self, *args, **kw):
        if len(args) > 0:
            raise ArgsNotAllowed(
                'U cant use args on this method. Use key=value'
            )
        for k, v in kw.iteritems():
            setattr(self, k, v)
        return function(self, **kw)

    return wrapper


class DatabaseScript(object):
    def __init__(self, instance, host=None, database=None,
                 plan=None, infra=None, disk_offering=None, 
                 need_move_data=False, need_master_variables=False):
        self.instance = instance
        self.host = host or instance.hostname
        self.infra = infra or self.instance.databaseinfra
        self.database = database or self.infra.databases.first()
        self.plan = plan or self.infra.plan
        self.disk_offering = disk_offering or self.infra.disk_offering
        self.need_move_data = need_move_data
        self.driver = self.infra.get_driver()
        self.need_master_variables = need_master_variables

    @property
    def base_context(self):
        context = {
            'DATABASENAME': self.database.name,
            'DBPASSWORD': self.infra.password,
            'HOST': self.host.hostname.split('.')[0],
            'HOSTADDRESS': self.instance.address,
            'ENGINE': self.plan.engine.engine_type.name,
            'MOVE_DATA': self.need_move_data,
            'DRIVER_NAME': self.driver.topology_name(),
            'DISK_SIZE_IN_GB': (self.disk_offering.size_gb()
                                if self.disk_offering else 8),
            'ENVIRONMENT': self.environment,
            'HAS_PERSISTENCE': self.plan.has_persistence,
            'IS_READ_ONLY': self.instance.read_only,
            'SSL_CONFIGURED': self.infra.ssl_configured,
            'SSL_MODE_ALLOW': self.infra.ssl_mode == self.infra.ALLOWTLS,
            'SSL_MODE_PREFER': self.infra.ssl_mode == self.infra.PREFERTLS,
            'SSL_MODE_REQUIRE': self.infra.ssl_mode == self.infra.REQUIRETLS,
        }

        if self.infra.ssl_configured:
            from workflow.steps.util.ssl import InfraSSLBaseName
            from workflow.steps.util.ssl import InstanceSSLBaseName
            infra_ssl = InfraSSLBaseName(self.instance)
            instance_ssl = InstanceSSLBaseName(self.instance)
            context['INFRA_SSL_CA'] = infra_ssl.ca_file_path
            context['INFRA_SSL_CERT'] = infra_ssl.cert_file_path
            context['INFRA_SSL_KEY'] = infra_ssl.key_file_path
            context['MASTER_SSL_CA'] = infra_ssl.master_ssl_ca
            context['INSTANCE_SSL_CA'] = instance_ssl.ca_file_path
            context['INSTANCE_SSL_CERT'] = instance_ssl.cert_file_path
            context['INSTANCE_SSL_KEY'] = instance_ssl.key_file_path

        context['configuration'] = self.get_configuration()

        return context

    def get_configuration(self):
        from physical.configurations import configuration_factory
        try:
            configuration = configuration_factory(
                self.infra, self.offering.memory_size_mb
            )
        except NotImplementedError:
            return None
        else:
            return configuration

    @property
    def initialization_variables(self):
        return self.instance.initialization_variables

    @property
    def master_variables(self):
        return self.driver.master_parameters(
            self.instance, self.infra.instances.first()
        )

    def make_template_context(self, extra_context=None):
        context = self.base_context
        if extra_context:
            context.update(extra_context)
        if self.need_master_variables:
            context.update(self.master_variables)
        return context

    def _render_template(self, context_dict, template_file):
        regex = re.compile(r'[\r]')
        script = regex.sub('', str(template_file))
        context = Context(context_dict)
        template = Template(script)
        return template.render(context)

    @update_instance_variables
    def init_database(self, *args, **kw):
        return self._render_template(
            context_dict=self.make_template_context(
                self.initialization_variables
            ),
            template_file=self.plan.script.initialization_template,
        )
