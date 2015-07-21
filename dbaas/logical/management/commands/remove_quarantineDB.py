from django.core.management.base import BaseCommand
import logging

from logical.models import Database


LOG = logging.getLogger(__name__)


class Command(BaseCommand):

    '''
        remove database automatically when quarantine date expired
    '''

    def handle(self, *args, **options):
        Database.purge_quarantine()
