from physical.models import DatabaseInfra
from maintenance.tasks import (region_migration_prepare, region_migration_finish,
                               region_migration_start)


class RegionMigrationUtil(object):

    dry_run = False

    @staticmethod
    def confirm(msg):
        return raw_input("{} (y/N) ".format(msg)).lower() == 'y'

    @staticmethod
    def get_infras(field, list_of_values):
        params = {
            '{}__in'.format(field): list_of_values
        }
        return DatabaseInfra.objects.filter(**params)

    @classmethod
    def default_exec(cls, func, resp, infras):
        if resp:
            for infra in infras:
                if cls.dry_run:
                    print infra
                else:
                    func(infra)

            print 'Done'
        else:
            print 'GoodBye'

    @classmethod
    def prepare_by(cls, field, list_of_values):
        """
            Perpare migration down TTL to 3 minutes

            params:
                - field: field name to loopkup
                - list_of_values: array with values

            Ex: RegionMigrationUtil.prepare_by('id', [1,2,3])
                the code will do DatabaseInfra.objects.filter(id__in=list_of_values)
            Ex: RegionMigrationUtil.prepare_by('name', ['infraname 1', 'infraname 2'])
                the code will do DatabaseInfra.objects.filter(name__in=list_of_values)
        """

        infras = cls.get_infras(field, list_of_values)
        resp = cls.confirm('Down TTL to 3 min of infras {}\n'.format(infras))
        cls.default_exec(func=region_migration_prepare, resp=resp, infras=infras)

    @classmethod
    def finish_by(cls, field, list_of_values):
        """
            Finish migration Up TTL to default

            params:
                - field: field name to loopkup
                - list_of_values: array with values

            Ex: RegionMigrationUtil.prepare_by('id', [1,2,3])
                the code will do DatabaseInfra.objects.filter(id__in=list_of_values)
            Ex: RegionMigrationUtil.prepare_by('name', ['infraname 1', 'infraname 2'])
                the code will do DatabaseInfra.objects.filter(name__in=list_of_values)
        """

        infras = cls.get_infras(field, list_of_values)
        resp = cls.confirm('Up TTL to default of infras {}\n'.format(infras))
        cls.default_exec(func=region_migration_finish, resp=resp, infras=infras)

    @classmethod
    def migrate_by(cls, field, list_of_values, instances_ids=None, since_step=None):
        """
            Migrate infras

            params:
                - field: field name to loopkup
                - list_of_values: array with values
                - instances_ids: array of instances to run if None we get all
                - since_step: specific step to continue

            Ex: RegionMigrationUtil.prepare_by('id', [1,2,3])
                the code will do DatabaseInfra.objects.filter(id__in=list_of_values)
            Ex: RegionMigrationUtil.prepare_by('name', ['infraname 1', 'infraname 2'])
                the code will do DatabaseInfra.objects.filter(name__in=list_of_values)
        """

        infras = cls.get_infras(field, list_of_values)
        resp = cls.confirm('Migrate infras {}\n'.format(infras))
        if resp:
            for infra in infras:
                if instances_ids:
                    instances = infra.instances.filter(id__in=instances_ids)
                else:
                    instances = infra.instances.all()

                sentinel = len(instances) == 5
                if sentinel:
                    instances = [instances[0], instances[2], instances[4]]
                params = dict(
                    infra=infra,
                    instances=instances,
                    **{'since_step': since_step} if since_step else {}
                )

                if cls.dry_run:
                    print params
                else:
                    region_migration_start.delay(**params)

            print 'Done'
        else:
            print 'GoodBye'
