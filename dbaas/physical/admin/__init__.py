# -*- coding:utf-8 -*-
from django.contrib import admin
from .. import models
from .databaseinfra import DatabaseInfraAdmin
from .engine import EngineAdmin
from .engine_type import EngineTypeAdmin
from .plan import PlanAdmin
from .host import HostAdmin
from .environment import EnvironmentAdmin
from .environment_group import EnvironmentGroupAdmin
from .replication_topology import ReplicationTopologyAdmin
from .disk_offering import DiskOfferingAdmin
from .parameter import ParameterAdmin
from .offering import OfferingAdmin
from .cloud import CloudAdmin
from .pool import PoolAdmin
from .core_replication_topology import CoreReplicationTopologyAdmin
from .ip import IpAdmin
from .vip import VipAdmin
from .vip_instance_group import VipInstanceGroupAdmin

admin.site.register(models.DatabaseInfra, DatabaseInfraAdmin)
admin.site.register(models.Engine, EngineAdmin)
admin.site.register(models.EngineType, EngineTypeAdmin)
admin.site.register(models.Plan, PlanAdmin)
admin.site.register(models.Host, HostAdmin)
admin.site.register(models.Offering, OfferingAdmin)
admin.site.register(models.Environment, EnvironmentAdmin)
admin.site.register(models.EnvironmentGroup, EnvironmentGroupAdmin)
admin.site.register(models.ReplicationTopology, ReplicationTopologyAdmin)
admin.site.register(models.DiskOffering, DiskOfferingAdmin)
admin.site.register(models.Parameter, ParameterAdmin)
admin.site.register(models.Cloud, CloudAdmin)
admin.site.register(models.Script)
admin.site.register(models.Pool, PoolAdmin)
admin.site.register(models.CoreReplicationTopology, CoreReplicationTopologyAdmin)
admin.site.register(models.Ip, IpAdmin)
admin.site.register(models.Vip, VipAdmin)
admin.site.register(models.VipInstanceGroup, VipInstanceGroupAdmin)
