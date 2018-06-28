class DisabledDatabase(EnvironmentError):
    def __init__(self, msg, url):
        self.url = url
        super(EnvironmentError, self).__init__(msg)


class DatabaseInQuarantineError(DisabledDatabase):
    def __init__(self, operation, url):
        msg = 'Database in quarantine and cannot do {}'.format(operation)
        super(DatabaseInQuarantineError, self).__init__(msg, url)


class DatabaseIsDeadError(DisabledDatabase):
    def __init__(self, operation, url):
        msg = 'Database is dead and cannot do {}'.format(operation)
        super(DatabaseIsDeadError, self).__init__(msg, url)


class BusyDatabaseError(DisabledDatabase):
    def __init__(self, url):
        msg = 'Database is being used by another task, please check your tasks'
        super(BusyDatabaseError, self).__init__(msg, url)


class MigrationDatabaseError(DisabledDatabase):
    def __init__(self, database, operation, url):
        msg = 'Database {} cannot do {} ' \
              'because it is being upgraded'.format(database, operation)
        super(MigrationDatabaseError, self).__init__(msg, url)


class NoResizeOption(EnvironmentError):
    def __init__(self, url):
        self.url = url
        msg = 'Database has no offerings availables'
        super(EnvironmentError, self).__init__(msg)


class DatabaseWithoutPersistence(DisabledDatabase):
    def __init__(self, database, operation, url):
        msg = 'Database {} cannot do {} ' \
              'because it is without persistence'.format(database, operation)
        super(DatabaseWithoutPersistence, self).__init__(msg, url)
