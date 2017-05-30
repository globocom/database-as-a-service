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
    MB_FORMATTER = 'MB'
    GB_FORMATTER = 'GB'

    def __init__(self, memory_size_mega):
        self._memory_size = memory_size_mega

    @property
    def memory_size_in_mb(self):
        return self._memory_size

    @property
    def memory_size_in_gb(self):
        return round(self._memory_size * self.MB_TO_GB_FACTOR, 2)

    def value_in_mb(self, value):
        return "{}{}".format(int(value), self.MB_FORMATTER)

    def value_in_gb(self, value):
        return "{}{}".format(int(value), self.GB_FORMATTER)

    def value_format(self, value):
        value_in_gb = value * self.MB_TO_GB_FACTOR
        if isinstance(value_in_gb, int) and value_in_gb >= 1:
            return self.value_in_gb(value_in_gb)
        return self.value_in_mb(value)


class ConfigurationRedis(ConfigurationBase):
    __ENGINE__ = 'redis'

    @property
    def max_memory(self):
        if self.memory_size_in_gb <= 1: #1G
            value = self.memory_size_in_mb / 2
        else:
            value = self.memory_size_in_mb * 0.75 # 3/4

        return self.value_format(value)

    @property
    def loglevel(self):
        return "warning"

    @property
    def save(self):
        return "7200 1 3600 10 1800 10000"

    @property
    def maxmemory(self):
        return self.max_memory


class ConfigurationMySQL(ConfigurationBase):
    __ENGINE__ = 'mysql'
    MB_FORMATTER = 'M'
    GB_FORMATTER = 'G'

    def compare_values(self, compares, values):
        for index, compare in enumerate(compares):
            if self.memory_size_in_mb <= compare:
                return values[index]
        return values[-1]

    def find_values(self, values):
        if len(values) == 5:
            return self.rule_of_fives(values)
        if len(values) == 6:
            return self.rule_of_six(values)

    def rule_of_fives(self, values):
        return self.compare_values([1024, 8192, 16384, 32768], values)

    def rule_of_six(self, values):
        return self.compare_values([512, 1024, 8192, 16384, 32768], values)

    @property
    def query_cache_size(self):
        value = self.find_values([32, 64, 512, 1024, 2048])
        return self.value_format(value)

    @property
    def max_allowed_packet(self):
        value = self.find_values([16, 32, 64, 512, 1024, 2048])
        return self.value_format(value)

    @property
    def sort_buffer_size(self):
        value = self.find_values([2, 5, 10, 80, 160, 320])
        return self.value_format(value)

    @property
    def tmp_table_size(self):
        value = self.find_values([16, 32, 64, 256, 512, 1024])
        return self.value_format(value)

    @property
    def max_heap_table_size(self):
        value = self.find_values([32, 64, 128, 512, 1024, 2048])
        return self.value_format(value)

    @property
    def max_binlog_size(self):
        value = 52428800 if self.memory_size_in_mb <= 2048 else 524288000
        return value

    @property
    def key_buffer_size(self):
        value = self.find_values([16, 32, 64, 512, 1024, 2048])
        return self.value_format(value)

    @property
    def myisam_sort_buffer_size(self):
        value = self.find_values([32, 64, 128, 1024, 2048, 4096])
        return self.value_format(value)

    @property
    def read_buffer_size(self):
        value = self.find_values([1, 2, 4, 32, 64, 128])
        return self.value_format(value)

    @property
    def read_rnd_buffer_size(self):
        value = self.find_values([4, 8, 16, 128, 256, 512])
        return self.value_format(value)

    @property
    def innodb_buffer_pool_size(self):
        value = self.compare_values(
            [512, 1024, 4096, 16384, 32768],
            [128, 256, 512, 4096, 8192, 16384]
        )
        return self.value_format(value)

    @property
    def innodb_log_file_size(self):
        value = 256 if self.memory_size_in_mb == 8192 else 64
        return self.value_format(value)

    @property
    def innodb_log_buffer_size(self):
        value = 64 if self.memory_size_in_mb == 8192 else 32
        return self.value_format(value)


class ConfigurationMongoDB(ConfigurationBase):
    __ENGINE__ = 'mongodb'

    @property
    def systemLog_quiet(self):
        return False

    def __getattr__(self, item):
        if '.' in item:
            item = item.replace('.', '_')

        return self.__getattribute__(item)
