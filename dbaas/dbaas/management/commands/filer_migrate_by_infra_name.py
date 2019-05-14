# coding: utf-8
from django.core.management.base import BaseCommand
from maintenance.scripts.filer_migrate import FilerMigrate
from logical.models import Database


class Command(BaseCommand):
    '''Migrate filer'''

    def handle(self, *args, **options):

        names = filter(lambda s: s, map(lambda s: s.strip(), args[0].split(',')))
        dbs = Database.objects.filter(databaseinfra__name__in=names)
        if not dbs:
            return "Nenhum banco encontrado"
        step = FilerMigrate(dbs)
        print "{} banco(s) para a migração: {}".format(
            len(dbs),
            ",".join(dbs.values_list('name', flat=True))
        )
        step.do()
        print "DONE"
