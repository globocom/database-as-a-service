from dbmonitor.provider import DBMonitorProvider
from dbaas_zabbix.provider import ZabbixProvider
import logging

LOG = logging.getLogger(__name__)

class MonitoringManager():
    
    @classmethod
    def create_monitoring(cls, databaseinfra):
        LOG.info("Creating monitoring...")
        ZabbixProvider().create_monitoring(dbinfra=databaseinfra)
        return DBMonitorProvider().create_dbmonitor_monitoring(databaseinfra)
            
    @classmethod 
    def remove_monitoring(cls, databaseinfra):
        LOG.info("Removing monitoring...")
        ZabbixProvider().destroy_monitoring(dbinfra=databaseinfra)
        return DBMonitorProvider().remove_dbmonitor_monitoring(databaseinfra)