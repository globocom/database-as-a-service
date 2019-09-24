# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

BASE_MODEL = {
    'created_at': datetime.datetime.now(),
    'updated_at': datetime.datetime.now()
}

ENGINE_TYPE_MYSQL_PERCONA = {
    'name': 'mysql_percona2',
    'is_in_memory': False
}

ENGINE_MYSQL_PERCONA = {
    'engine_type': ENGINE_TYPE_MYSQL_PERCONA['name'],
    'version': '5.7.25', 'path': '', 'template_name': '',
    'user_data_script': '', 'engine_upgrade_option': None,
    'has_users': True, 'write_node_description': 'Master',
    'read_node_description': 'Slave',
    'major_version': 5,
    'minor_version': 7,
    'is_active': True,
    'initial_patch': 25
}

REPLICATION_TOPOLOGIES_MYSQL_PERCONA = [
    {
        "name": "MySQL Percona Single 5.7.25_2",
        "engine": None,
        "class_path": "drivers.replication_topologies.mysql_percona.MySQLPerconaSingle",
        "details": "HA: No",
        "has_horizontal_scalability": False,
        "can_resize_vm": True,
        "can_clone_db": True,
        "can_switch_master": True,
        "can_upgrade_db": True,
        "can_change_parameters": True,
        "can_reinstall_vm": True,
        "can_setup_ssl": True,
        "script": "MySQL 5.7",
        "parameter": []
    },
    {
        "name": "MySQL Percona FoxHA 5.7.25_2",
        "engine": None,
        "class_path": "drivers.replication_topologies.mysql_percona.MySQLPerconaFoxHA",
        "details": "HA: FoxHA",
        "has_horizontal_scalability": False,
        "can_resize_vm": True,
        "can_clone_db": True,
        "can_switch_master": True,
        "can_upgrade_db": True,
        "can_change_parameters": True,
        "can_reinstall_vm": True,
        "can_setup_ssl": True,
        "script": "MySQL FoxHA 5.7",
        "parameter": []
    },
    {
        "name": "AWS MySQL Percona FoxHA 5.7.25_2",
        "engine": None,
        "class_path": "drivers.replication_topologies.mysql_percona.MySQLPerconaFoxHAAWS",
        "details": "MySQLPerconaFoxHAAWS",
        "has_horizontal_scalability": False,
        "can_resize_vm": True,
        "can_clone_db": True,
        "can_switch_master": True,
        "can_upgrade_db": True,
        "can_change_parameters": True,
        "can_reinstall_vm": False,
        "can_setup_ssl": True,
        "script": "MySQL FoxHA 5.7",
        "parameter": []
    }
]

PLANS_MYSQL_PERCONA = [
    {
        "name": "MySQL Percona Single 5.7.25_2",
        "description": "",
        "is_active": True,
        "is_ha": False,
        "engine": None,
        "replication_topology": None,
        "has_persistence": True,
        "environments": "dev",
        "provider": 1,
        "max_db_size": 500,
        "engine_equivalent_plan": None,
        "disk_offering": "Small",
        "migrate_plan": None,
        "stronger_offering": "c1m1 (1 CPU + 1 GB)",
        "weaker_offering": None,
        "dns_plan": {
            "dnsapi_vm_domain": "globoi.com",
            "dnsapi_database_domain": "mysql.globoi.com"
        }
    },
    {
        "name": "MySQL Percona FOXHA Small - 5.7.25_2",
        "description": "",
        "is_active": True,
        "is_ha": True,
        "engine": None,
        "replication_topology": None,
        "has_persistence": True,
        "environments": "prod",
        "provider": 1,
        "max_db_size": 512,
        "engine_equivalent_plan": None,
        "disk_offering": "Small",
        "migrate_plan": None,
        "stronger_offering": "c1m1 (1 CPU + 1 GB)",
        "weaker_offering": "c1m0.5 (1 CPU + 0.5 GB)",
        "dns_plan": {
            "dnsapi_vm_domain": "globoi.com",
            "dnsapi_database_domain": "mysql.globoi.com"
        }
    },
    {
        "name": "MySQL Percona FOXHA Small - 5.7.25 - aws-prod_2",
        "description": "",
        "is_active": True,
        "is_ha": True,
        "engine": None,
        "replication_topology": None,
        "has_persistence": True,
        "environments": 'aws-prod',
        "provider": 1,
        "max_db_size": 500,
        "engine_equivalent_plan": None,
        "disk_offering": "Small",
        "migrate_plan": None,
        "stronger_offering": "c1m0.5 (1 CPU + 0.5 GB)",
        "weaker_offering": "c1m10.5 (1 CPU + 0.5 GB)",
        "dns_plan": {
            "dnsapi_vm_domain": "globoi.com",
            "dnsapi_database_domain": "mysql.globoi.com"
        }
    }
]



class Migration(DataMigration):

    def create_engine_type(self, orm):
        engine_type = orm.EngineType()
        engine_type.created_at = BASE_MODEL['created_at']
        engine_type.updated_at = BASE_MODEL['updated_at']
        engine_type.name = ENGINE_TYPE_MYSQL_PERCONA['name']
        engine_type.is_in_memory = ENGINE_TYPE_MYSQL_PERCONA['is_in_memory']
        engine_type.save()

        return engine_type

    def create_engine(self, orm):
        engine = orm.Engine()
        engine.created_at = BASE_MODEL['created_at']
        engine.updated_at = BASE_MODEL['updated_at']
        engine.engine_type = self.engine_type
        engine.version = ENGINE_MYSQL_PERCONA['version']
        engine.path = ENGINE_MYSQL_PERCONA['path']
        engine.template_name = ENGINE_MYSQL_PERCONA['template_name']
        engine.user_data_script = ENGINE_MYSQL_PERCONA['user_data_script']
        engine.engine_upgrade_option = ENGINE_MYSQL_PERCONA['engine_upgrade_option']
        engine.has_users = ENGINE_MYSQL_PERCONA['has_users']
        engine.write_node_description = ENGINE_MYSQL_PERCONA['write_node_description']
        engine.read_node_description = ENGINE_MYSQL_PERCONA['read_node_description']
        engine.major_version = ENGINE_MYSQL_PERCONA['major_version']
        engine.minor_version = ENGINE_MYSQL_PERCONA['minor_version']
        engine.is_active = ENGINE_MYSQL_PERCONA['is_active']
        engine.save()

        self.create_initial_engine_patch(
            orm, engine, ENGINE_MYSQL_PERCONA['initial_patch']
        )

        return engine

    def create_initial_engine_patch(self, orm, engine, initial_patch):
        engine_patch = orm.EnginePatch()
        engine_patch.created_at = BASE_MODEL['created_at']
        engine_patch.updated_at = BASE_MODEL['updated_at']
        engine_patch.engine = engine
        engine_patch.patch_version = initial_patch
        engine_patch.is_initial_patch = True
        engine_patch.save()

    def create_replication_topology(self, orm, rep_top):
        replication_topology = orm.ReplicationTopology()
        replication_topology.created_at = BASE_MODEL['created_at']
        replication_topology.updated_at = BASE_MODEL['updated_at']
        replication_topology.name = rep_top['name']
        replication_topology.class_path = rep_top['class_path']
        replication_topology.details = rep_top['details']
        replication_topology.has_horizontal_scalability = rep_top['has_horizontal_scalability']
        replication_topology.can_resize_vm = rep_top['can_resize_vm']
        replication_topology.can_clone_db = rep_top['can_clone_db']
        replication_topology.can_switch_master = rep_top['can_switch_master']
        replication_topology.can_upgrade_db = rep_top['can_upgrade_db']
        replication_topology.can_change_parameters = rep_top['can_change_parameters']
        replication_topology.can_reinstall_vm = rep_top['can_reinstall_vm']
        replication_topology.can_setup_ssl = rep_top['can_setup_ssl']
        replication_topology.script = orm.Script.objects.filter(name=rep_top['script']).first()
        replication_topology.save()

        replication_topology.engine.add(self.engine)

        mysql_parameters = orm.Parameter.objects.filter(engine_type__name__contains='mysql').all()
        replication_topology.parameter.add(*mysql_parameters)

        return replication_topology

    def create_plan(self, orm, current_rep_top, plan_data):
        plan = orm.Plan()
        plan.created_at = BASE_MODEL['created_at']
        plan.updated_at = BASE_MODEL['updated_at']
        plan.name = plan_data['name']
        plan.description = plan_data['description']
        plan.is_active = plan_data['is_active']
        plan.is_ha = plan_data['is_ha']
        plan.engine = self.engine
        plan.replication_topology = current_rep_top
        plan.has_persistence = plan_data['has_persistence']
        plan.provider = plan_data['provider']
        plan.max_db_size = plan_data['max_db_size']
        plan.engine_equivalent_plan = plan_data['engine_equivalent_plan']
        plan.disk_offering = orm.DiskOffering.objects.filter(name=plan_data['disk_offering']).first()
        plan.migrate_plan = plan_data['migrate_plan']
        plan.stronger_offering = orm.Offering.objects.filter(name=plan_data['stronger_offering']).first()
        plan.weaker_offering = orm.Offering.objects.filter(name=plan_data['weaker_offering']).first()
        plan.save()

        environment = orm.Environment.objects.filter(name=plan_data['environments']).first()
        plan.environments.add(environment)

        return plan

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName".
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        self.engine_type = self.create_engine_type(orm)
        self.engine = self.create_engine(orm)

        for index, rep_top in enumerate(REPLICATION_TOPOLOGIES_MYSQL_PERCONA):
            current_rep_top = self.create_replication_topology(orm, rep_top)
            self.create_plan(orm, current_rep_top, PLANS_MYSQL_PERCONA[index])

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'physical.cloud': {
            'Meta': {'object_name': 'Cloud'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.databaseinfra': {
            'Meta': {'object_name': 'DatabaseInfra'},
            'backup_hour': ('django.db.models.fields.IntegerField', [], {}),
            'capacity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'database_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'disk_offering': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['physical.DiskOffering']"}),
            'endpoint': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'endpoint_dns': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Engine']"}),
            'engine_patch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['physical.EnginePatch']"}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_vm_created': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'name_prefix': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'name_stamp': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'per_database_size_mbytes': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Plan']"}),
            'ssl_configured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'physical.databaseinfraparameter': {
            'Meta': {'unique_together': "((u'databaseinfra', u'parameter'),)", 'object_name': 'DatabaseInfraParameter'},
            'applied_on_database': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_value': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'databaseinfra': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['physical.DatabaseInfra']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['physical.Parameter']"}),
            'reset_default_value': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'physical.diskoffering': {
            'Meta': {'object_name': 'DiskOffering'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'size_kb': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.engine': {
            'Meta': {'ordering': "(u'engine_type__name', u'version')", 'unique_together': "((u'version', u'engine_type'),)", 'object_name': 'Engine'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'engines'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.EngineType']"}),
            'engine_upgrade_option': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'backwards_engine'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['physical.Engine']"}),
            'has_users': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'major_version': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'minor_version': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'read_node_description': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'template_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_data_script': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'write_node_description': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'physical.enginepatch': {
            'Meta': {'object_name': 'EnginePatch'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'patchs'", 'to': u"orm['physical.Engine']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_initial_patch': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'patch_path': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'patch_version': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'required_disk_size_gb': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.enginetype': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'EngineType'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_in_memory': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.environment': {
            'Meta': {'object_name': 'Environment'},
            'cloud': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'environment_cloud'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Cloud']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'migrate_environment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'migrate_to'", 'null': 'True', 'to': u"orm['physical.Environment']"}),
            'min_of_zones': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.environmentgroup': {
            'Meta': {'object_name': 'EnvironmentGroup'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'environments': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'groups'", 'symmetrical': 'False', 'to': u"orm['physical.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.host': {
            'Meta': {'object_name': 'Host'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'future_host': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['physical.Host']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255'}),
            'monitor_url': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'offering': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['physical.Offering']", 'null': 'True'}),
            'os_description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'null': 'True', 'blank': 'True'}),
            'root_size_gb': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'physical.instance': {
            'Meta': {'unique_together': "((u'address', u'port'),)", 'object_name': 'Instance'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'databaseinfra': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'to': u"orm['physical.DatabaseInfra']"}),
            'dns': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'future_instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['physical.Instance']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'to': u"orm['physical.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'read_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shard': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'total_size_in_bytes': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'used_size_in_bytes': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'physical.offering': {
            'Meta': {'object_name': 'Offering'},
            'cpus': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'environments': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'offerings'", 'symmetrical': 'False', 'to': u"orm['physical.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'memory_size_mb': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.parameter': {
            'Meta': {'ordering': "(u'engine_type__name', u'name')", 'unique_together': "((u'name', u'engine_type'),)", 'object_name': 'Parameter'},
            'allowed_values': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'custom_method': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'dynamic': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'enginetype'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.EngineType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parameter_type': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.plan': {
            'Meta': {'object_name': 'Plan'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'disk_offering': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'plans'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['physical.DiskOffering']"}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'plans'", 'to': u"orm['physical.Engine']"}),
            'engine_equivalent_plan': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'backwards_plan'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['physical.Plan']"}),
            'environments': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'plans'", 'symmetrical': 'False', 'to': u"orm['physical.Environment']"}),
            'has_persistence': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_ha': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'max_db_size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'migrate_plan': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'migrate_to'", 'null': 'True', 'to': u"orm['physical.Plan']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'provider': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'replication_topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'replication_topology'", 'null': 'True', 'to': u"orm['physical.ReplicationTopology']"}),
            'stronger_offering': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'main_offerings'", 'null': 'True', 'to': u"orm['physical.Offering']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'weaker_offering': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'weaker_offerings'", 'null': 'True', 'to': u"orm['physical.Offering']"})
        },
        u'physical.planattribute': {
            'Meta': {'object_name': 'PlanAttribute'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'plan_attributes'", 'to': u"orm['physical.Plan']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'physical.replicationtopology': {
            'Meta': {'object_name': 'ReplicationTopology'},
            'can_change_parameters': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_clone_db': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_reinstall_vm': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_resize_vm': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_setup_ssl': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_switch_master': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_upgrade_db': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'class_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'replication_topologies'", 'symmetrical': 'False', 'to': u"orm['physical.Engine']"}),
            'has_horizontal_scalability': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parameter': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'replication_topologies'", 'blank': 'True', 'to': u"orm['physical.Parameter']"}),
            'script': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'replication_topologies'", 'null': 'True', 'to': u"orm['physical.Script']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.script': {
            'Meta': {'object_name': 'Script'},
            'configuration': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initialization': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'metric_collector': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'start_database': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'start_replication': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.topologyparametercustomvalue': {
            'Meta': {'unique_together': "((u'topology', u'parameter'),)", 'object_name': 'TopologyParameterCustomValue'},
            'attr_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'topology_custom_values'", 'to': u"orm['physical.Parameter']"}),
            'topology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'param_custom_values'", 'to': u"orm['physical.ReplicationTopology']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.vip': {
            'Meta': {'object_name': 'Vip'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'infra': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'vips'", 'to': u"orm['physical.DatabaseInfra']"}),
            'original_vip': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['physical.Vip']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.volume': {
            'Meta': {'object_name': 'Volume'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'volumes'", 'to': u"orm['physical.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'total_size_kb': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'used_size_kb': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['physical']
    symmetrical = True
