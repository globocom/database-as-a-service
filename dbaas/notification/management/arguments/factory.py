class ArgumentsTo(object):

    def __init__(self, request):
        self.KEY = ''
        self.args = request.kwargs

    def build(self):
        raise NotImplementedError


class ArgumentsToCreateDatabase(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToCreateDatabase, self).__init__(request)
        self.KEY = 'notification.tasks.create_database'

    def build(self):
        return [
            "Database: {}".format(self.args['name']),
            "Environment: {}".format(self.args['environment']),
            "Project: {}".format(self.args['project']),
            "Plan: {}".format(self.args['Plan']),
        ]


class ArgumentsToResizeDatabase(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToResizeDatabase, self).__init__(request)
        self.KEY = 'notification.tasks.resize_database'

    def build(self):
        return [
            "Database: {}".format(self.args['database'].name),
            "New VM Offering: {}".format(self.args['cloudstackpack']),
        ]


class ArgumentsToDiskResize(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToDiskResize, self).__init__(request)
        self.KEY = 'notification.tasks.database_disk_resize'

    def build(self):
        return [
            "Database: {}".format(self.args['database'].name),
            "New Disk Offering: {}".format(self.args['disk_offering']),
        ]


class ArgumentsToRestoreSnapshot(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToRestoreSnapshot, self).__init__(request)
        self.KEY = 'backup.tasks.restore_snapshot'

    def build(self):
        return [
            "Database: {}".format(self.args['database'].name),
            "Description: Restoring to an older version.It will finish soon",
        ]


class ArgumentsToDestroyDatabase(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToDestroyDatabase, self).__init__(request)
        self.KEY = 'notification.tasks.destroy_database'

    def build(self):
        return [
            "Database: {}".format(self.args['database'].name),
            "User: {}".format(self.args['user']),
        ]


class ArgumentsToCloneDatabase(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToCloneDatabase, self).__init__(request)
        self.KEY = 'notification.tasks.clone_database'

    def build(self):
        return [
            "Database: {}".format(self.args['origin_database'].name),
            "Clone: {}".format(self.args['clone_name']),
            "Environment: {}".format(self.args['environment']),
            "Plan: {}".format(self.args['Plan']),
        ]


class ArgumentsToAnalyzeDatabases(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToAnalyzeDatabases, self).__init__(request)
        self.KEY = 'dbaas_services.analyzing.tasks.analyze.analyze_databases'

    def build(self):
        return [
            "Description: Analyzing all databases",
        ]


class ArgumentsToUpgrade(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToUpgrade, self).__init__(request)
        self.KEY = 'notification.tasks.upgrade_mongodb_24_to_30'

    def build(self):
        return [
            "Database: {}".format(self.args['database'].name),
        ]


class ArgumentsToUnbindAddress(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToUnbindAddress, self).__init__(request)
        self.KEY = 'dbaas_aclapi.tasks.unbind_address_on_database'

    def build(self):
        return [
            "Removing Binds For: {}".format(self.args['database_bind']),
            "From Database: {}".format(self.args['database_bind'].database),
        ]


class ArgumentsToBindAddress(ArgumentsTo):

    def __init__(self, request):
        super(ArgumentsToBindAddress, self).__init__(request)
        self.KEY = 'dbaas_aclapi.tasks.bind_address_on_database'

    def build(self):
        return [
            "Creating Binds For: {}".format(self.args['database_bind']),
            "From Database: {}".format(self.args['database_bind'].database),
        ]