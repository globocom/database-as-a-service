from django.conf import settings

class BaseEngine(object):
    """
    BaseEngine interface
    """
    
    @staticmethod
    def is_engine_available(name):
        return name in settings.INSTALLED_APPS

    @staticmethod
    def factory(name):

        if name.lower() == "mongodb": 
            return MongoDB()

        assert 0, "Bad Engine Type: " + name

    
    def url(self):
        raise NotImplementedError()