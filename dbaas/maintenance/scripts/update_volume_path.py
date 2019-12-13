from backup.models import Volume
from workflow.steps.util.volume_provider import VolumeProviderBase


for vol in Volume.objects.all():
    vol_inst = vol.host and vol.host.instances.first()
    if not vol_inst:
        continue
    provider = VolumeProviderBase(vol_inst)
    vol_path = provider.get_path(vol)
    if not vol_path:
        continue
    for snap in vol.backups.all():
        snap.volume_path = vol_path
        snap.save()
