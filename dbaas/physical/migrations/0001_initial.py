# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
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
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('engine_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'plans', to=orm['physical.EngineType'])),
        ))
        db.send_create_signal(u'physical', ['Plan'])

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

        # Adding model 'Instance'
        db.create_table(u'physical_instance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=406, blank=True)),
            ('engine', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'instances', on_delete=models.PROTECT, to=orm['physical.Engine'])),
            ('plan', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'instances', on_delete=models.PROTECT, to=orm['physical.Plan'])),
        ))
        db.send_create_signal(u'physical', ['Instance'])

        # Adding model 'Node'
        db.create_table(u'physical_node', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('port', self.gf('django.db.models.fields.IntegerField')()),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'nodes', to=orm['physical.Instance'])),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'2', max_length=2)),
        ))
        db.send_create_signal(u'physical', ['Node'])

        # Adding unique constraint on 'Node', fields ['address', 'port']
        db.create_unique(u'physical_node', ['address', 'port'])


    def backwards(self, orm):
        # Removing unique constraint on 'Node', fields ['address', 'port']
        db.delete_unique(u'physical_node', ['address', 'port'])

        # Removing unique constraint on 'Engine', fields ['version', 'engine_type']
        db.delete_unique(u'physical_engine', ['version', 'engine_type_id'])

        # Deleting model 'EngineType'
        db.delete_table(u'physical_enginetype')

        # Deleting model 'Engine'
        db.delete_table(u'physical_engine')

        # Deleting model 'Plan'
        db.delete_table(u'physical_plan')

        # Deleting model 'PlanAttribute'
        db.delete_table(u'physical_planattribute')

        # Deleting model 'Instance'
        db.delete_table(u'physical_instance')

        # Deleting model 'Node'
        db.delete_table(u'physical_node')


    models = {
        u'physical.engine': {
            'Meta': {'unique_together': "((u'version', u'engine_type'),)", 'object_name': 'Engine'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'engines'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.EngineType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'physical.enginetype': {
            'Meta': {'object_name': 'EngineType'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.instance': {
            'Meta': {'object_name': 'Instance'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Engine']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Plan']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'physical.node': {
            'Meta': {'unique_together': "((u'address', u'port'),)", 'object_name': 'Node'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'nodes'", 'to': u"orm['physical.Instance']"}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'2'", 'max_length': '2'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'physical.plan': {
            'Meta': {'object_name': 'Plan'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'plans'", 'to': u"orm['physical.EngineType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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