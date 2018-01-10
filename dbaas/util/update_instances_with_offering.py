# coding: utf-8


class UpdateInstances(object):

    @staticmethod
    def do():
        from dbaas_cloudstack.models import DatabaseInfraOffering
        from dbaas_cloudstack.models import PlanAttr

        infra_offerings = DatabaseInfraOffering.objects.all()

        for infra_offering in infra_offerings:
            plan_attr = PlanAttr.objects.get(plan=infra_offering.databaseinfra.plan)
            strong_offering = infra_offering.offering
            weaker_offering = plan_attr.get_weaker_offering()

            for host in infra_offering.databaseinfra.hosts:
                host.offering = strong_offering if host.database_instance() else weaker_offering
                host.save()

    @staticmethod
    def see_offering():
        from logical.models import Database

        for db in Database.objects.all():
            print db.name
            for i in db.infra.hosts:
                print i.offering
