# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Environment'
        db.create_table(u'physical_environment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal(u'physical', ['Environment'])

        # Adding model 'EngineType'
        db.create_table(u'physical_enginetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal(u'physical', ['EngineType'])

        # Adding model 'Engine'
        db.create_table(u'physical_engine', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('engine_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'engines', on_delete=models.PROTECT, to=orm['physical.EngineType'])),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('template_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('user_data_script', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'physical', ['Engine'])

        # Adding unique constraint on 'Engine', fields ['version', 'engine_type']
        db.create_unique(u'physical_engine', ['version', 'engine_type_id'])

        # Adding model 'Plan'
        db.create_table(u'physical_plan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('engine_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'plans', to=orm['physical.EngineType'])),
        ))
        db.send_create_signal(u'physical', ['Plan'])

        # Adding M2M table for field environments on 'Plan'
        m2m_table_name = db.shorten_name(u'physical_plan_environments')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('plan', models.ForeignKey(orm[u'physical.plan'], null=False)),
            ('environment', models.ForeignKey(orm[u'physical.environment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['plan_id', 'environment_id'])

        # Adding model 'PlanAttribute'
        db.create_table(u'physical_planattribute', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('plan', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'plan_attributes', to=orm['physical.Plan'])),
        ))
        db.send_create_signal(u'physical', ['PlanAttribute'])

        # Adding model 'DatabaseInfra'
        db.create_table(u'physical_databaseinfra', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=406, blank=True)),
            ('engine', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'databaseinfras', on_delete=models.PROTECT, to=orm['physical.Engine'])),
            ('plan', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'databaseinfras', on_delete=models.PROTECT, to=orm['physical.Plan'])),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'databaseinfras', on_delete=models.PROTECT, to=orm['physical.Environment'])),
        ))
        db.send_create_signal(u'physical', ['DatabaseInfra'])

        # Adding model 'Host'
        db.create_table(u'physical_host', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'physical', ['Host'])

        # Adding model 'Instance'
        db.create_table(u'physical_instance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('port', self.gf('django.db.models.fields.IntegerField')()),
            ('databaseinfra', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'instances', to=orm['physical.DatabaseInfra'])),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_arbiter', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('hostname', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['physical.Host'])),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'2', max_length=2)),
        ))
        db.send_create_signal(u'physical', ['Instance'])

        # Adding unique constraint on 'Instance', fields ['address', 'port']
        db.create_unique(u'physical_instance', ['address', 'port'])


    def backwards(self, orm):
        # Removing unique constraint on 'Instance', fields ['address', 'port']
        db.delete_unique(u'physical_instance', ['address', 'port'])

        # Removing unique constraint on 'Engine', fields ['version', 'engine_type']
        db.delete_unique(u'physical_engine', ['version', 'engine_type_id'])

        # Deleting model 'Environment'
        db.delete_table(u'physical_environment')

        # Deleting model 'EngineType'
        db.delete_table(u'physical_enginetype')

        # Deleting model 'Engine'
        db.delete_table(u'physical_engine')

        # Deleting model 'Plan'
        db.delete_table(u'physical_plan')

        # Removing M2M table for field environments on 'Plan'
        db.delete_table(db.shorten_name(u'physical_plan_environments'))

        # Deleting model 'PlanAttribute'
        db.delete_table(u'physical_planattribute')

        # Deleting model 'DatabaseInfra'
        db.delete_table(u'physical_databaseinfra')

        # Deleting model 'Host'
        db.delete_table(u'physical_host')

        # Deleting model 'Instance'
        db.delete_table(u'physical_instance')


    models = {
        u'physical.databaseinfra': {
            'Meta': {'object_name': 'DatabaseInfra'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Engine']"}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Plan']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'physical.engine': {
            'Meta': {'unique_together': "((u'version', u'engine_type'),)", 'object_name': 'Engine'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'engines'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.EngineType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'template_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_data_script': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'physical.enginetype': {
            'Meta': {'object_name': 'EngineType'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.environment': {
            'Meta': {'object_name': 'Environment'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.host': {
            'Meta': {'object_name': 'Host'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.instance': {
            'Meta': {'unique_together': "((u'address', u'port'),)", 'object_name': 'Instance'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'databaseinfra': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'to': u"orm['physical.DatabaseInfra']"}),
            'hostname': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['physical.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_arbiter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'2'", 'max_length': '2'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.plan': {
            'Meta': {'object_name': 'Plan'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'plans'", 'to': u"orm['physical.EngineType']"}),
            'environments': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['physical.Environment']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.planattribute': {
            'Meta': {'object_name': 'PlanAttribute'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'plan_attributes'", 'to': u"orm['physical.Plan']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['physical']