from dbaas_dbmonitor.provider import DBMonitorProvider
from dbaas_zabbix.provider import ZabbixProvider
import logging

LOG = logging.getLogger(__name__)

class MonitoringManager():
    
    @classmethod
    def create_monitoring(cls, databaseinfra):
        try:
            LOG.info("Creating monitoring...")
            #ZabbixProvider().create_monitoring(dbinfra=databaseinfra)
            return DBMonitorProvider().create_dbmonitor_monitoring(databaseinfra)
        except Exception, e:
            LOG.warn("Exception: %s" % e)
            return None
            
    @classmethod 
    def remove_monitoring(cls, databaseinfra):
        try:
            LOG.info("Removing monitoring...")
            #ZabbixProvider().destroy_monitoring(dbinfra=databaseinfra)
            return DBMonitorProvider().remove_dbmonitor_monitoring(databaseinfra)
        except Exception, e:
            LOG.warn("Exception: %s" % e)
            return None
