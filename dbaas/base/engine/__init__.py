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
