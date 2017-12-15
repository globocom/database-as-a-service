from django_services.service.exceptions import InternalException


class GenericDriverError(InternalException):

    """ Exception raises when any kind of problem happens when executing operations on databaseinfra """

    def __init__(self, message=None):
        self.message = message

    def __unicode__(self):
        return "%s: %s" % (type(self).__name__, self.message)

    def __str__(self):
        return b"%s: %s" % (type(self).__name__, self.message)

    def __repr__(self):
        return b"%s: %s" % (type(self).__name__, self.message)


class ConnectionError(GenericDriverError):
    pass


class AuthenticationError(ConnectionError):
    pass


class DatabaseAlreadyExists(InternalException):
    pass


class DatabaseDoesNotExist(InternalException):
    pass


class CredentialAlreadyExists(InternalException):
    pass


class InvalidCredential(InternalException):
    pass


class ReplicationError(GenericDriverError):
    pass


class ReplicationNotRunningError(ReplicationError):

    def __init__(self):
        super(ReplicationNotRunningError, self).__init__(
            "Replication is not running"
        )


class ReplicationNoPrimary(ReplicationError):
    pass


class ReplicationNoInstances(ReplicationError):
    pass
