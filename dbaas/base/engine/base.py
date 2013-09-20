

class BaseEngine(object):
    """
    BaseEngine interface
    """

    def __init__(self, *args, **kwargs):

        if 'instance' in kwargs:
            self.instance = kwargs.get('instance')
            self.node = self.instance.node
        else:
            raise TypeError(_("Instance is not defined"))

    def url(self):
        raise NotImplementedError()

    def port(self):
        return self.node.port

    def address(self):
        return self.node.address

    def user(self):
        return self.instance.user

    def password(self):
        return self.instance.password

    def status(self):
        raise NotImplementedError()

    def create_user(self, credential, database):
        raise NotImplementedError()

    def remove_user(self, credential):
        raise NotImplementedError()

    def create_database(self, database):
        raise NotImplementedError()

    def remove_database(self, database):
        raise NotImplementedError()

    def list_databases(self):
        """list databases in a instance"""
        raise NotImplementedError()

