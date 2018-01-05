# coding: utf-8


class UpdateInstances(object):

    @staticmethod
    def do():
        from dbaas_cloudstack.models import DatabaseInfraOffering
        from dbaas_cloudstack.models import PlanAttr
        from physical.models import Instance

        infra_offerings = DatabaseInfraOffering.objects.all()

        for infra_offering in infra_offerings:
            plan_attr = PlanAttr.objects.get(plan=infra_offering.databaseinfra.plan)
            strong_offering = infra_offering.offering
            weaker_offering = plan_attr.get_weaker_offering()

            for instance in infra_offering.databaseinfra.instances.all():
                if (instance.instance_type == Instance.MONGODB_ARBITER or
                     instance.instance_type == Instance.Sentinel):
                    instance.offering = weaker_offering
                else:
                    instance.oferring = strong_offering

                instance.save()
