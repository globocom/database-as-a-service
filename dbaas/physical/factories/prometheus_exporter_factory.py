import logging

from physical.service.prometheus_exporter import RedisExporter, MongoDBExporter, MySQLExporter

LOG = logging.getLogger(__name__)


def get_exporter(databaseinfra):  # instancia a classe de exporter correta de acordo com a engine da infra
    LOG.info("Returning correct prometheus exporter instance for infra %s", databaseinfra.name)

    if 'redis' in databaseinfra.engine_name.lower():
        return RedisExporter(databaseinfra.environment)
    elif 'mongo' in databaseinfra.engine_name.lower():
        return MongoDBExporter(databaseinfra.environment)
    elif 'mysql' in databaseinfra.engine_name.lower():
        return MySQLExporter(databaseinfra.environment)

    raise NotImplementedError('Prometheus Exporter for infra engine not implemented')
