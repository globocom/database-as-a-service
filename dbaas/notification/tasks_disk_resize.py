# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.core.exceptions import ObjectDoesNotExist


def update_disk(database, address, total_size, used_size, task):
    try:
        volume = database.update_host_disk_used_size(
            host_address=address, used_size_kb=used_size, total_size_kb=total_size
        )
        if not volume:
            raise EnvironmentError("Instance {} do not have disk".format(address))
    except ObjectDoesNotExist:
        task.add_detail(
            message="{} not found for: {}".format(address, database.name), level=3
        )
        return False
    except Exception as error:
        task.add_detail(
            message="Could not update disk size used: {}".format(error), level=3
        )
        return False

    task.add_detail(
        message="Used disk size updated. NFS: {}".format(volume.identifier), level=3
    )
    return True
