from __future__ import absolute_import, unicode_literals
import factory
from datetime import datetime
from physical.tests.factory import InstanceFactory, VolumeFactory
from backup.models import Snapshot


class SnapshotFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Snapshot

    start_at = datetime.now()
    type = Snapshot.SNAPSHOPT
    status = Snapshot.SUCCESS
    instance = factory.SubFactory(InstanceFactory)
    database_name = factory.Sequence(lambda n: 'database_{0}'.format(n))
    size = 1024
    snapshopt_id = factory.Sequence(lambda n: 'id_{0}'.format(n))
    snapshot_name = factory.Sequence(lambda n: 'name_{0}'.format(n))
    volume = factory.SubFactory(VolumeFactory)
