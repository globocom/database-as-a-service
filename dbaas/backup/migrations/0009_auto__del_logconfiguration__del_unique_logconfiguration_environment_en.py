# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'LogConfiguration', fields ['environment', 'engine_type']
        db.delete_unique(u'backup_logconfiguration', ['environment_id', 'engine_type_id'])

        # Deleting model 'LogConfiguration'
        db.delete_table(u'backup_logconfiguration')


    def backwards(self, orm):
        # Adding model 'LogConfiguration'
        db.create_table(u'backup_logconfiguration', (
            ('mount_point_path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('log_path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('cron_minute', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('retention_days', self.gf('django.db.models.fields.SmallIntegerField')(default=7, max_length=2)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('clean_backup_log_script', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('backup_log_script', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('cron_hour', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('filer_path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['physical.Environment'])),
            ('config_backup_log_script', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('engine_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['physical.EngineType'])),
        ))
        db.send_create_signal(u'backup', ['LogConfiguration'])

        # Adding unique constraint on 'LogConfiguration', fields ['environment', 'engine_type']
        db.create_unique(u'backup_logconfiguration', ['environment_id', 'engine_type_id'])


    models = {
        u'backup.backupgroup': {
            'Meta': {'object_name': 'BackupGroup'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'backup.snapshot': {
            'Meta': {'object_name': 'Snapshot'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'database_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'end_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'backup_environment'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['physical.Environment']"}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'export_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'backups'", 'null': 'True', 'to': u"orm['backup.BackupGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'backup_instance'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['physical.Instance']"}),
            'is_automatic': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'purge_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'snapshopt_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'snapshot_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'start_at': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.databaseinfra': {
            'Meta': {'object_name': 'DatabaseInfra'},
            'capacity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'database_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'disk_offering': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['physical.DiskOffering']"}),
            'endpoint': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'endpoint_dns': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Engine']"}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_vm_created': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'name_prefix': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'name_stamp': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'per_database_size_mbytes': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Plan']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
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
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'read_node_description': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'template_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_data_script': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'write_node_description': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100', 'null': 'True', 'blank': 'True'})
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'migrate_environment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'migrate_to'", 'null': 'True', 'to': u"orm['physical.Environment']"}),
            'min_of_zones': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
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
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'offerings'", 'to': u"orm['physical.Environment']"}),
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
        u'physical.replicationtopology': {
            'Meta': {'object_name': 'ReplicationTopology'},
            'can_change_parameters': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_clone_db': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_reinstall_vm': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'can_resize_vm': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'start_database': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'start_replication': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['backup']