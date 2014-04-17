from dbmonitor.provider import DBMonitorProvider
import logging

LOG = logging.getLogger(__name__)

class MonitoringManager():
    
    @classmethod
    def create_monitoring(cls, databaseinfra):
        LOG.info("Creating monitoring...")
        return DBMonitorProvider().create_dbmonitor_monitoring(databaseinfra)
            
    @classmethod 
    def remove_monitoring(cls, databaseinfra):
        LOG.info("Removing monitoring...")
        return DBMonitorProvider().remove_dbmonitor_monitoring(databaseinfra)