from dbaas_nfsaas.models import HostAttr
from physical.models import Volume


for nfsaas in HostAttr.objects.all():
    volume = Volume()
    volume.host = nfsaas.host
    volume.identifier = nfsaas.nfsaas_export_id
    volume.is_active = nfsaas.is_active
    volume.total_size_kb = nfsaas.nfsaas_size_kb
    volume.used_size_kb = nfsaas.nfsaas_used_size_kb
    print(volume.host, volume.identifier)
    volume.save()
    for instance in nfsaas.host.instances.all():
        for backup in instance.backup_instance.all():
            backup.volume = volume
            backup.save()
