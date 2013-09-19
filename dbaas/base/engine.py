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
        
        engine_name = name.lower()
        
        if engine_name == "mongodb":
            if BaseEngine.is_engine_available(engine_name):
                return MongoDB()
            else:
                raise NotImplementedError()

        assert 0, "Bad Engine Type: " + name

    
    def url(self):
        raise NotImplementedError()