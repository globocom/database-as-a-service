from physical.models import Plan, Environment, DiskOfferingType, PlanAttribute


def update_gcp_to_ssd():
    gcp_environments = Environment.objects.filter(name__icontains='gcp')
    plans = Plan.objects.filter(environments__in=gcp_environments)

    disk_offering_type_ssd = DiskOfferingType.objects.filter(identifier='SSD').first()

    for plan in plans:
        plan.disk_offering_type = disk_offering_type_ssd
        plan.save()

        attribute = PlanAttribute.objects.filter(name='disk_type', plan=plan).first()
        if attribute:
            attribute.value = 'pd-ssd'
            attribute.save()
