# TODO: Move this rules to model or be smarter
import sys
import inspect
from models import TopologyParameterCustomValue


def configuration_factory(databaseinfra, memory_size):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and '__ENGINE__' in obj.__dict__:
            if obj.__ENGINE__ == databaseinfra.engine.name:
                return obj(databaseinfra, memory_size)
    raise NotImplementedError


def configuration_exists(engine_name, parameter_name):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and '__ENGINE__' in obj.__dict__:
            if obj.__ENGINE__ == engine_name:
                parameter_name = parameter_name.replace('-', '_')
                if parameter_name in obj.__dict__:
                    return True
    return False


class ParameterObject(object):
    def __init__(self, value, default):
        self.value = str(value)
        self.default = str(default)


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

    @property
    def memory_size_in_bytes(self):
        return self._memory_size * 1024 * 1024

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

    def __getattribute__(self, item):
        if item == 'databaseinfra':
            return object.__getattribute__(self, item)

        topology = self.databaseinfra.plan.replication_topology
        try:
            attribute = TopologyParameterCustomValue.objects.get(
                topology=topology, parameter__name=item.replace("_", "-")
            )
            return object.__getattribute__(self, attribute.attr_name)
        except TopologyParameterCustomValue.DoesNotExist:
            return object.__getattribute__(self, item)


class ConfigurationRedis(ConfigurationBase):
    __ENGINE__ = 'redis'

    @property
    def maxmemory(self):
        parameter_name = inspect.stack()[0][3]
        if self.memory_size_in_gb <= 1:
            value = self.memory_size_in_bytes / 2
        else:
            value = self.memory_size_in_bytes * 0.75

        default = int(value)
        return self.get_parameter(parameter_name, default)

    @property
    def appendonly(self):
        parameter_name = inspect.stack()[0][3]
        if self.databaseinfra.plan.has_persistence:
            default = 'yes'
        else:
            default = 'no'
        return self.get_parameter(parameter_name, default)

    @property
    def maxmemory_policy(self):
        parameter_name = inspect.stack()[0][3]
        if self.databaseinfra.plan.has_persistence:
            default = 'volatile-lru'
        else:
            default = 'allkeys-lru'
        return self.get_parameter(parameter_name, default)

    @property
    def loglevel(self):
        parameter_name = inspect.stack()[0][3]
        default = 'notice'
        return self.get_parameter(parameter_name, default)

    @property
    def databases(self):
        parameter_name = inspect.stack()[0][3]
        default = '1'
        return self.get_parameter(parameter_name, default)

    @property
    def timeout(self):
        parameter_name = inspect.stack()[0][3]
        default = 0
        return self.get_parameter(parameter_name, default)

    @property
    def rdbcompression(self):
        parameter_name = inspect.stack()[0][3]
        default = 'yes'
        return self.get_parameter(parameter_name, default)

    @property
    def rdbchecksum(self):
        parameter_name = inspect.stack()[0][3]
        default = 'yes'
        return self.get_parameter(parameter_name, default)

    @property
    def slave_serve_stale_data(self):
        parameter_name = inspect.stack()[0][3]
        default = 'yes'
        return self.get_parameter(parameter_name, default)

    @property
    def slave_read_only(self):
        parameter_name = inspect.stack()[0][3]
        default = 'yes'
        return self.get_parameter(parameter_name, default)

    @property
    def maxclients(self):
        parameter_name = inspect.stack()[0][3]
        default = 10000
        return self.get_parameter(parameter_name, default)

    @property
    def appendfsync(self):
        parameter_name = inspect.stack()[0][3]
        default = 'everysec'
        return self.get_parameter(parameter_name, default)

    @property
    def no_appendfsync_on_rewrite(self):
        parameter_name = inspect.stack()[0][3]
        default = 'no'
        return self.get_parameter(parameter_name, default)

    @property
    def auto_aof_rewrite_percentage(self):
        parameter_name = inspect.stack()[0][3]
        default = 100
        return self.get_parameter(parameter_name, default)

    @property
    def auto_aof_rewrite_min_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 1073741824
        return self.get_parameter(parameter_name, default)

    @property
    def lua_time_limit(self):
        parameter_name = inspect.stack()[0][3]
        default = 5000
        return self.get_parameter(parameter_name, default)

    @property
    def slowlog_log_slower_than(self):
        parameter_name = inspect.stack()[0][3]
        default = 10000
        return self.get_parameter(parameter_name, default)

    @property
    def slowlog_max_len(self):
        parameter_name = inspect.stack()[0][3]
        default = 1024
        return self.get_parameter(parameter_name, default)

    @property
    def hash_max_ziplist_entries(self):
        parameter_name = inspect.stack()[0][3]
        default = 512
        return self.get_parameter(parameter_name, default)

    @property
    def hash_max_ziplist_value(self):
        parameter_name = inspect.stack()[0][3]
        default = 64
        return self.get_parameter(parameter_name, default)

    @property
    def set_max_intset_entries(self):
        parameter_name = inspect.stack()[0][3]
        default = 512
        return self.get_parameter(parameter_name, default)

    @property
    def zset_max_ziplist_entries(self):
        parameter_name = inspect.stack()[0][3]
        default = 128
        return self.get_parameter(parameter_name, default)

    @property
    def zset_max_ziplist_value(self):
        parameter_name = inspect.stack()[0][3]
        default = 64
        return self.get_parameter(parameter_name, default)

    @property
    def activerehashing(self):
        parameter_name = inspect.stack()[0][3]
        default = 'yes'
        return self.get_parameter(parameter_name, default)

    @property
    def repl_ping_slave_period(self):
        parameter_name = inspect.stack()[0][3]
        default = 1
        return self.get_parameter(parameter_name, default)

    @property
    def repl_timeout(self):
        parameter_name = inspect.stack()[0][3]
        default = 60
        return self.get_parameter(parameter_name, default)

    @property
    def repl_disable_tcp_nodelay(self):
        parameter_name = inspect.stack()[0][3]
        default = 'no'
        return self.get_parameter(parameter_name, default)

    @property
    def repl_backlog_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 1048576
        return self.get_parameter(parameter_name, default)

    @property
    def repl_backlog_ttl(self):
        parameter_name = inspect.stack()[0][3]
        default = 3600
        return self.get_parameter(parameter_name, default)

    @property
    def client_output_buffer_limit_normal(self):
        parameter_name = inspect.stack()[0][3]
        default = "0 0 0"
        return self.get_parameter(parameter_name, default)

    @property
    def client_output_buffer_limit_slave(self):
        parameter_name = inspect.stack()[0][3]
        default = "268435456 67108864 60"
        return self.get_parameter(parameter_name, default)

    @property
    def client_output_buffer_limit_pubsub(self):
        parameter_name = inspect.stack()[0][3]
        default = "33554432 8388608 60"
        return self.get_parameter(parameter_name, default)

    @property
    def cluster_enabled(self):
        return 'no'

    @property
    def cluster_enabled_true(self):
        return 'yes'


class ConfigurationMySQL(ConfigurationBase):
    __ENGINE__ = 'mysql'

    @property
    def query_cache_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 0
        return self.get_parameter(parameter_name, default)

    @property
    def max_allowed_packet(self):
        parameter_name = inspect.stack()[0][3]
        default = 4194304
        return self.get_parameter(parameter_name, default)

    @property
    def sort_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        default = int(self.memory_size_in_bytes / 204.8)
        return self.get_parameter(parameter_name, default)

    @property
    def tmp_table_size(self):
        parameter_name = inspect.stack()[0][3]
        default = int(self.memory_size_in_bytes / 64)
        return self.get_parameter(parameter_name, default)

    @property
    def max_heap_table_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 16777216
        return self.get_parameter(parameter_name, default)

    @property
    def max_binlog_size(self):
        parameter_name = inspect.stack()[0][3]
        if self.memory_size_in_mb < 2048:
            default = 52428800
        elif self.memory_size_in_mb < 8192:
            default = 104857600
        elif self.memory_size_in_mb < 32768:
            default = 262144000
        else:
            default = 524288000
        return self.get_parameter(parameter_name, default)

    @property
    def key_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 8388608
        return self.get_parameter(parameter_name, default)

    @property
    def myisam_sort_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 8388608
        return self.get_parameter(parameter_name, default)

    @property
    def read_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 131072
        return self.get_parameter(parameter_name, default)

    @property
    def read_rnd_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 262144
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_buffer_pool_size(self):
        parameter_name = inspect.stack()[0][3]
        if self.memory_size_in_mb < 1024:
            default = self.memory_size_in_bytes / 4
        elif self.memory_size_in_mb < 8192:
            default = self.memory_size_in_bytes / 2
        else:
            default = (self.memory_size_in_bytes * 3) / 4
        default = int(default)
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_log_file_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 50331648
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_log_buffer_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 8388608
        return self.get_parameter(parameter_name, default)

    @property
    def binlog_format(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ROW'
        return self.get_parameter(parameter_name, default)

    @property
    def transaction_isolation(self):
        parameter_name = inspect.stack()[0][3]
        default = 'READ-COMMITTED'
        return self.get_parameter(parameter_name, default)

    @property
    def default_storage_engine(self):
        parameter_name = inspect.stack()[0][3]
        default = 'InnoDB'
        return self.get_parameter(parameter_name, default)

    @property
    def default_tmp_storage_engine(self):
        parameter_name = inspect.stack()[0][3]
        default = 'InnoDB'
        return self.get_parameter(parameter_name, default)

    @property
    def character_set_server(self):
        parameter_name = inspect.stack()[0][3]
        default = 'utf8'
        return self.get_parameter(parameter_name, default)

    @property
    def max_connections(self):
        parameter_name = inspect.stack()[0][3]
        default = 1000
        return self.get_parameter(parameter_name, default)

    @property
    def max_connect_errors(self):
        parameter_name = inspect.stack()[0][3]
        default = 999999
        return self.get_parameter(parameter_name, default)

    @property
    def thread_cache_size(self):
        parameter_name = inspect.stack()[0][3]
        default = 32
        return self.get_parameter(parameter_name, default)

    @property
    def table_open_cache(self):
        parameter_name = inspect.stack()[0][3]
        default = 4096
        return self.get_parameter(parameter_name, default)

    @property
    def query_cache_type(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def sync_binlog(self):
        parameter_name = inspect.stack()[0][3]
        default = 1
        return self.get_parameter(parameter_name, default)

    @property
    def expire_logs_days(self):
        parameter_name = inspect.stack()[0][3]
        default = 3
        return self.get_parameter(parameter_name, default)

    @property
    def long_query_time(self):
        parameter_name = inspect.stack()[0][3]
        default = '1.000000'
        return self.get_parameter(parameter_name, default)

    @property
    def slow_query_log(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_autoextend_increment(self):
        parameter_name = inspect.stack()[0][3]
        default = 8
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_file_per_table(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_lock_wait_timeout(self):
        parameter_name = inspect.stack()[0][3]
        default = 50
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_flush_log_at_trx_commit(self):
        parameter_name = inspect.stack()[0][3]
        default = 1
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_thread_concurrency(self):
        parameter_name = inspect.stack()[0][3]
        default = 16
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_max_dirty_pages_pct(self):
        parameter_name = inspect.stack()[0][3]
        default = 90
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_max_purge_lag(self):
        parameter_name = inspect.stack()[0][3]
        default = 0
        return self.get_parameter(parameter_name, default)

    @property
    def explicit_defaults_for_timestamp(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def performance_schema(self):
        parameter_name = inspect.stack()[0][3]
        if self.memory_size_in_mb < 8192:
            default = 'OFF'
        else:
            default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def thread_stack(self):
        parameter_name = inspect.stack()[0][3]
        default = 196608
        return self.get_parameter(parameter_name, default)

    @property
    def thread_concurrency(self):
        parameter_name = inspect.stack()[0][3]
        default = 16
        return self.get_parameter(parameter_name, default)

    @property
    def log_slave_updates(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_log_files_in_group(self):
        parameter_name = inspect.stack()[0][3]
        default = 3
        return self.get_parameter(parameter_name, default)

    @property
    def innodb_flush_method(self):
        parameter_name = inspect.stack()[0][3]
        default = 'O_DIRECT'
        return self.get_parameter(parameter_name, default)

    @property
    def skip_external_locking(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def skip_name_resolve(self):
        parameter_name = inspect.stack()[0][3]
        default = 'ON'
        return self.get_parameter(parameter_name, default)

    @property
    def wait_timeout(self):
        parameter_name = inspect.stack()[0][3]
        default = 28800
        return self.get_parameter(parameter_name, default)

    @property
    def interactive_timeout(self):
        parameter_name = inspect.stack()[0][3]
        default = 28800
        return self.get_parameter(parameter_name, default)

    @property
    def log_bin_trust_function_creators(self):
        parameter_name = inspect.stack()[0][3]
        default = 'OFF'
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

    @property
    def oplogSize(self):
        parameter_name = inspect.stack()[0][3]
        default = 512
        return self.get_parameter(parameter_name, default)

    @property
    def quiet(self):
        parameter_name = inspect.stack()[0][3]
        default = 'false'
        return self.get_parameter(parameter_name, default)

    @property
    def logLevel(self):
        parameter_name = inspect.stack()[0][3]
        default = 0
        return self.get_parameter(parameter_name, default)

    @property
    def wiredTiger_engineConfig_cacheSizeGB(self):
        parameter_name = inspect.stack()[0][3]
        if self.memory_size_in_mb < 2564:
            cache_mb = 256
        else:
            cache_mb =  (self.memory_size_in_mb - 1024) / 2
        default = round(cache_mb / 1024.0, 2)
        return self.get_parameter(parameter_name, default)

