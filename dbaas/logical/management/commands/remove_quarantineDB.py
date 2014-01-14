from django.core.management.base import BaseCommand
from datetime import date, timedelta
import logging

from logical.models import Database
from system.models import Configuration


LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
        remove database automatically when quarantine date expired
    '''

    def handle(self, *args, **options):
        quarantine_time = Configuration.get_by_name_as_int('quarantine_retention_days')
        quarantine_time_dt = date.today() - timedelta(days=quarantine_time)
        databases = Database.objects.filter(is_in_quarantine=True, quarantine_dt__lte=quarantine_time_dt)
        for database in databases:
            database.delete()
            LOG.info("The database %s was deleted, because it was set to quarentine %d days ago" % (database.name, quarantine_time))
