class ArgumentsTo(object):

    def __init__(self, args):
        self.KEY = ''
        self.args = args

    def build(self):
        raise NotImplementedError


class ArgumentsToCreateDatabase(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToCreateDatabase, self).__init__(args)
        self.KEY = 'notification.tasks.create_database'

    def build(self):
        return [
            "Database name: {}".format(self.args['name']),
            "Environment: {}".format(self.args['environment']),
            "Project: {}".format(self.args['project']),
            "Plan: {}".format(self.args['plan']),
        ]


class ArgumentsToResizeDatabase(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToResizeDatabase, self).__init__(args)
        self.KEY = 'notification.tasks.resize_database'

    def build(self):
        return [
            "Database name: {}".format(self.args['database'].name),
            "New VM Offering: {}".format(self.args['cloudstackpack']),
        ]


class ArgumentsToUpgradeDatabase(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToUpgradeDatabase, self).__init__(args)
        self.KEY = 'notification.tasks.upgrade_database'

    def build(self):
        return [
            "Database name: {}".format(self.args['database'].name),
            "Target plan: {}".format(self.args['target_plan']),
        ]


class ArgumentsToDiskResize(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToDiskResize, self).__init__(args)
        self.KEY = 'notification.tasks.database_disk_resize'

    def build(self):
        return [
            "Database name: {}".format(self.args['database'].name),
            "New Disk Offering: {}".format(self.args['disk_offering']),
        ]


class ArgumentsToRestoreSnapshot(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToRestoreSnapshot, self).__init__(args)
        self.KEY = 'backup.tasks.restore_snapshot'

    def build(self):
        return [
            "Database name: {}".format(self.args['database'].name),
            "Description: Restoring to an older version. It will finish soon.",
        ]


class ArgumentsToDestroyDatabase(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToDestroyDatabase, self).__init__(args)
        self.KEY = 'notification.tasks.destroy_database'

    def build(self):
        return [
            "Database name: {}".format(self.args['database'].name),
            "User: {}".format(self.args['user']),
        ]


class ArgumentsToCloneDatabase(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToCloneDatabase, self).__init__(args)
        self.KEY = 'notification.tasks.clone_database'

    def build(self):
        return [
            "Database name: {}".format(self.args['origin_database'].name),
            "Clone: {}".format(self.args['clone_name']),
            "Environment: {}".format(self.args['environment']),
            "Plan: {}".format(self.args['plan']),
        ]


class ArgumentsToAnalyzeDatabases(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToAnalyzeDatabases, self).__init__(args)
        self.KEY = 'dbaas_services.analyzing.tasks.analyze.analyze_databases'

    def build(self):
        return [
            "Description: Analyzing all databases",
        ]


class ArgumentsToUpgrade(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToUpgrade, self).__init__(args)
        self.KEY = 'notification.tasks.upgrade_mongodb_24_to_30'

    def build(self):
        return [
            "Database name: {}".format(self.args['database'].name),
        ]


class ArgumentsToUnbindAddress(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToUnbindAddress, self).__init__(args)
        self.KEY = 'dbaas_aclapi.tasks.unbind_address_on_database'

    def build(self):
        return [
            "Removing Binds For: {}".format(self.args['database_bind']),
            "From Database: {}".format(self.args['database_bind'].database),
        ]


class ArgumentsToBindAddress(ArgumentsTo):

    def __init__(self, args):
        super(ArgumentsToBindAddress, self).__init__(args)
        self.KEY = 'dbaas_aclapi.tasks.bind_address_on_database'

    def build(self):
        return [
            "Creating Binds For: {}".format(self.args['database_bind']),
            "From Database: {}".format(self.args['database_bind'].database),
        ]
