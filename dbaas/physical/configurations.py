# TODO: Move this rules to model or be smarter
import sys
import inspect


def configuration_factory(databaseinfra, memory_size):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and '__ENGINE__' in obj.__dict__:
            if obj.__ENGINE__ == databaseinfra.engine.name:
                return obj(databaseinfra, memory_size)
    raise NotImplementedError


class ParameterObject(object):
    def __init__(self, value, default):
        self.value = value
        self.default = default


class ConfigurationBase(object):
    __ENGINE__ = 'None'
    MB_TO_GB_FACTOR = 1.0 / 1024
    MB_FORMATTER = 'MB'
    GB_FORMATTER = 'GB'

    def __init__(self, databaseinfra, memory_size_mega):
        self.databaseinfra = databaseinfra
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

    def get_parameter(self, parameter_name, default):
        value = self.databaseinfra.get_parameter_value_by_parameter_name(
            parameter_name=parameter_name
        )
        if not value:
            value = default
        return ParameterObject(value, default)


class ConfigurationRedis(ConfigurationBase):
    __ENGINE__ = 'redis'

    @property
    def maxmemory(self):
        parameter_name = inspect.stack()[0][3]
        if self.memory_size_in_gb <= 1: #1G
            value = self.memory_size_in_mb / 2
        else:
            value = self.memory_size_in_mb * 0.75 # 3/4

        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def loglevel(self):
        parameter_name = inspect.stack()[0][3]
        default = "warning"
        return self.get_parameter(parameter_name, default)

    @property
    def save(self):
        parameter_name = inspect.stack()[0][3]
        default = "7200 1 3600 10 1800 10000"
        return self.get_parameter(parameter_name, default)


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
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([32, 64, 512, 1024, 2048])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def max_allowed_packet(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([16, 32, 64, 512, 1024, 2048])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def sort_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([2, 5, 10, 80, 160, 320])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def tmp_table_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([16, 32, 64, 256, 512, 1024])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def max_heap_table_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([32, 64, 128, 512, 1024, 2048])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def max_binlog_size(self):
        parameter_name = inspect.stack()[0][3]
        value = 52428800 if self.memory_size_in_mb <= 2048 else 524288000
        default = value
        return self.get_parameter(parameter_name, default)

    @property
    def key_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([16, 32, 64, 512, 1024, 2048])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def myisam_sort_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([32, 64, 128, 1024, 2048, 4096])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def read_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([1, 2, 4, 32, 64, 128])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def read_rnd_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.find_values([4, 8, 16, 128, 256, 512])
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_buffer_pool_size(self):
        parameter_name = inspect.stack()[0][3]
        value = self.compare_values(
            [512, 1024, 4096, 16384, 32768],
            [128, 256, 512, 4096, 8192, 16384]
        )
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_log_file_size(self):
        parameter_name = inspect.stack()[0][3]
        value = 256 if self.memory_size_in_mb == 8192 else 64
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_log_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        value = 64 if self.memory_size_in_mb == 8192 else 32
        default = self.value_format(value)
        return self.get_parameter(parameter_name, default)


class ConfigurationMongoDB(ConfigurationBase):
    __ENGINE__ = 'mongodb'

    @property
    def systemLog_quiet(self):
        parameter_name = inspect.stack()[0][3]
        default = False
        return self.get_parameter(parameter_name, default)

    def __getattr__(self, item):
        if '.' in item:
            item = item.replace('.', '_')

        return self.__getattribute__(item)
