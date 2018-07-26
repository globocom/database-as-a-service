class ArgumentsTo(object):
    KEY = ''

    def __init__(self, args):
        self.args = args

    def build(self):
        raise NotImplementedError

    @property
    def database_name(self):
        return self.args['database'].name

    def get_database_arg(self):
        return "Database: {}".format(self.database_name)

    def get_environment_arg(self):
        return "Environment: {}".format(self.args['environment'])

    def get_plan_arg(self):
        return "Plan: {}".format(self.args['plan'])

    def get_project_arg(self):
        return "Project: {}".format(self.args['project'])

    def get_user_arg(self):
        return "User: {}".format(self.args['user'])

    def get_clone_arg(self):
        return "Clone: {}".format(self.args['clone_name'])


class ArgumentsToCreateDatabase(ArgumentsTo):
    KEY = 'notification.tasks.create_database'

    def build(self):
        return [
            self.get_database_arg(),
            self.get_environment_arg(),
            self.get_project_arg(),
            self.get_plan_arg(),
        ]

    @property
    def database_name(self):
        return self.args['name']


class ArgumentsToResizeDatabase(ArgumentsTo):
    KEY = 'notification.tasks.resize_database'

    def build(self):
        return [
            self.get_database_arg(),
            "New VM Offering: {}".format(self.args['offering']),
        ]


class ArgumentsToUpgradeDatabase(ArgumentsTo):
    KEY = 'notification.tasks.upgrade_database'

    def build(self):
        return [
            self.get_database_arg(),
            "Target plan: {}".format(
                self.args['database'].databaseinfra.plan.engine_equivalent_plan
            ),
        ]


class ArgumentsToReinstallVM(ArgumentsTo):
    KEY = 'notification.tasks.reinstall_vm'

    def build(self):
        return [
            self.get_database_arg(),
            "Instance: {}".format(
                self.args['instance']
            ),
        ]


class ArgumentsToDiskResize(ArgumentsTo):
    KEY = 'notification.tasks.database_disk_resize'

    def build(self):
        return [
            self.get_database_arg(),
            "New Disk Offering: {}".format(self.args['disk_offering']),
        ]


class ArgumentsToRestoreSnapshot(ArgumentsTo):
    KEY = 'backup.tasks.restore_snapshot'

    def build(self):
        return [
            self.get_database_arg(),
            "Description: Restoring to an older version. It will finish soon.",
        ]


class ArgumentsToDestroyDatabase(ArgumentsTo):
    KEY = 'notification.tasks.destroy_database'

    def build(self):
        return [
            self.get_database_arg(),
            self.get_user_arg(),
        ]


class ArgumentsToCloneDatabase(ArgumentsTo):
    KEY = 'notification.tasks.clone_database'

    def build(self):
        return [
            self.get_database_arg(),
            self.get_clone_arg(),
            self.get_environment_arg(),
            self.get_plan_arg(),
        ]

    @property
    def database_name(self):
        return self.args['origin_database'].name


class ArgumentsToAnalyzeDatabases(ArgumentsTo):
    KEY = 'dbaas_services.analyzing.tasks.analyze.analyze_databases'

    def build(self):
        return [
            "Description: Analyzing all databases",
        ]


class ArgumentsToUpgradeMongo24To30(ArgumentsTo):
    KEY = 'notification.tasks.upgrade_mongodb_24_to_30'

    def build(self):
        return [
            self.get_database_arg(),
        ]


class ArgumentsToUnbindAddress(ArgumentsTo):
    KEY = 'dbaas_aclapi.tasks.unbind_address_on_database'

    def build(self):
        return [
            "Removing Binds For: {}".format(self.args['database_bind']),
            self.get_database_arg(),
        ]

    @property
    def database_name(self):
        return self.args['database_bind'].database.name


class ArgumentsToBindAddress(ArgumentsTo):
    KEY = 'dbaas_aclapi.tasks.bind_address_on_database'

    def build(self):
        return [
            "Creating Binds For: {}".format(self.args['database_bind']),
            self.get_database_arg(),
        ]

    @property
    def database_name(self):
        return self.args['database_bind'].database.name


class ArgumentsToAddInstancesToDatabase(ArgumentsTo):
    KEY = 'notification.tasks.add_instances_to_database'

    def build(self):
        return [
            "Add new instances on {}".format(self.get_database_arg()),
            "Number of instances: {}".format(self.args['number_of_instances'])
        ]


class ArgumentsToRemoveReadOnlyInstance(ArgumentsTo):
    KEY = 'notification.tasks.remove_readonly_instance'

    def build(self):
        return [
            "Removing read only instance from {}".format(self.get_database_arg()),
            "Instance: {}".format(self.args['instance'])
        ]
