from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from physical.models import Engine
from physical.tests import factory
from account.models import Role, Team


class Command(BaseCommand):

    '''Populate database w/ basic local infrastructure
    assumed you are running: mongodb 2.4.5 on 127.0.0.1:27017
    and its mongo has an user on admin database: admin / 123456
    '''

    def handle(self, *args, **options):
        # engine was created by initial_data.yml
        my_engine = Engine.objects.get(
            version='2.4.5', engine_type__name='mongodb')

        my_host = factory.HostFactory(hostname='localhost')
        my_env = factory.EnvironmentFactory(name='laboratory')
        my_plan = factory.PlanFactory(
            name='small', engine_type=my_engine.engine_type, environments=[my_env])
        my_infradb = factory.DatabaseInfraFactory(
            name='local_infra',
            plan=my_plan,
            environment=my_env,
            engine=my_engine,
            capacity=10)
        factory.InstanceFactory(databaseinfra=my_infradb, hostname=my_host)

        my_role = Role.objects.get_or_create(name="role_dba")[0]
        my_team = Team.objects.get_or_create(name="my team", role=my_role)[0]
        my_admin = User.objects.create_superuser(
            'admin', email='admin@admin.com', password='123456')
        my_team.users.add(my_admin)
