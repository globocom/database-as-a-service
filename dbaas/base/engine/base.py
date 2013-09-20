from django.conf import settings


class BaseEngine(object):
    """
    BaseEngine interface
    """

    @staticmethod
    def is_engine_available(name):
        return name in settings.INSTALLED_APPS

    @staticmethod
    def factory(name, node):

        engine_name = name.lower()

        # TODO: import Engines dynamically
        if engine_name == "mongodb":
            if BaseEngine.is_engine_available(engine_name):
                from mongodb import MongoDB
                return MongoDB(node=node)
            else:
                raise NotImplementedError()

        assert 0, "Bad Engine Type: " + name


    def __init__(self, *args, **kwargs):

        if 'node' in kwargs:
            self.node = kwargs.get('node')

    def url(self):
        raise NotImplementedError()

    def port(self):
        raise NotImplementedError()

    def address(self):
        raise NotImplementedError()

    def user(self):
        raise NotImplementedError()

    def password(self):
        raise NotImplementedError()

    def status(self, instance):
        raise NotImplementedError()

    def create_user(self, credential, database):
        raise NotImplementedError()

    def remove_user(self, credential):
        raise NotImplementedError()

    def create_database(self, database):
        raise NotImplementedError()

    def remove_database(self, database):
        raise NotImplementedError()

    def list_databases(self, instance):
        """list databases in a instance"""
        raise NotImplementedError()
