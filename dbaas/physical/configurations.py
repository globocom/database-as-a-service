# TODO: Move this rules to model or be smarter
import sys
import inspect


def configuration_factory(engine, memory_size):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and '__ENGINE__' in obj.__dict__:
            if obj.__ENGINE__ == engine:
                return obj(memory_size)
    raise NotImplementedError


class ConfigurationBase(object):
    __ENGINE__ = 'None'
    MB_TO_GB_FACTOR = 1.0 / 1024

    def __init__(self, memory_size_mega):
        self._memory_size = memory_size_mega

    @property
    def memory_size_in_mb(self):
        return self._memory_size

    @property
    def memory_size_in_gb(self):
        return round(self._memory_size * self.MB_TO_GB_FACTOR, 2)

    def value_in_mb(self, value):
        return "{}MB".format(int(value))


class ConfigurationRedis(ConfigurationBase):
    __ENGINE__ = 'redis'

    @property
    def max_memory(self):
        if self.memory_size_in_gb <= 1: #1G
            value = self.memory_size_in_mb / 2
        else:
            value = self.memory_size_in_mb * 0.75 # 3/4

        return self.value_in_mb(value)
