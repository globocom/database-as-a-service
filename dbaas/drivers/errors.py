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

    """ Raised when there is any problem to connect on databaseinfra """
    pass


class AuthenticationError(ConnectionError):

    """ Raised when there is any problem authenticating on databaseinfra """
    pass


class DatabaseAlreadyExists(InternalException):

    """ Raised when database already exists in datainfra """
    pass


class DatabaseDoesNotExist(InternalException):

    """ Raised when there is no requested database """
    pass


class CredentialAlreadyExists(InternalException):

    """ Raised when credential already exists in database """
    pass


class InvalidCredential(InternalException):

    """ Raised when credential no more exists in database """
    pass

