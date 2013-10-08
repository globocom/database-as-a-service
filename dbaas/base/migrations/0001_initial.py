# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Environment'
        db.create_table(u'base_environment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'base', ['Environment'])

        # Adding model 'Node'
        db.create_table(u'base_node', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('port', self.gf('django.db.models.fields.IntegerField')()),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'nodes', on_delete=models.PROTECT, to=orm['base.Environment'])),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'2', max_length=2)),
        ))
        db.send_create_signal(u'base', ['Node'])

        # Adding unique constraint on 'Node', fields ['address', 'port']
        db.create_unique(u'base_node', ['address', 'port'])

        # Adding model 'EngineType'
        db.create_table(u'base_enginetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal(u'base', ['EngineType'])

        # Adding model 'Engine'
        db.create_table(u'base_engine', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('engine_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'engines', on_delete=models.PROTECT, to=orm['base.EngineType'])),
        ))
        db.send_create_signal(u'base', ['Engine'])

        # Adding unique constraint on 'Engine', fields ['version', 'engine_type']
        db.create_unique(u'base_engine', ['version', 'engine_type_id'])

        # Adding model 'Instance'
        db.create_table(u'base_instance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=406, blank=True)),
            ('node', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['base.Node'], unique=True, on_delete=models.PROTECT)),
            ('engine', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'instances', on_delete=models.PROTECT, to=orm['base.Engine'])),
        ))
        db.send_create_signal(u'base', ['Instance'])

        # Adding model 'Database'
        db.create_table(u'base_database', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'databases', on_delete=models.PROTECT, to=orm['base.Instance'])),
        ))
        db.send_create_signal(u'base', ['Database'])

        # Adding model 'Credential'
        db.create_table(u'base_credential', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 8, 0, 0), auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=406)),
            ('database', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'credentials', to=orm['base.Database'])),
        ))
        db.send_create_signal(u'base', ['Credential'])


    def backwards(self, orm):
        # Removing unique constraint on 'Engine', fields ['version', 'engine_type']
        db.delete_unique(u'base_engine', ['version', 'engine_type_id'])

        # Removing unique constraint on 'Node', fields ['address', 'port']
        db.delete_unique(u'base_node', ['address', 'port'])

        # Deleting model 'Environment'
        db.delete_table(u'base_environment')

        # Deleting model 'Node'
        db.delete_table(u'base_node')

        # Deleting model 'EngineType'
        db.delete_table(u'base_enginetype')

        # Deleting model 'Engine'
        db.delete_table(u'base_engine')

        # Deleting model 'Instance'
        db.delete_table(u'base_instance')

        # Deleting model 'Database'
        db.delete_table(u'base_database')

        # Deleting model 'Credential'
        db.delete_table(u'base_credential')


    models = {
        u'base.credential': {
            'Meta': {'object_name': 'Credential'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'database': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'credentials'", 'to': u"orm['base.Database']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'base.database': {
            'Meta': {'object_name': 'Database'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databases'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.Instance']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        },
        u'base.engine': {
            'Meta': {'unique_together': "((u'version', u'engine_type'),)", 'object_name': 'Engine'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'engine_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'engines'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.EngineType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'base.enginetype': {
            'Meta': {'object_name': 'EngineType'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        },
        u'base.environment': {
            'Meta': {'object_name': 'Environment'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        },
        u'base.instance': {
            'Meta': {'object_name': 'Instance'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instances'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.Engine']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'node': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['base.Node']", 'unique': 'True', 'on_delete': 'models.PROTECT'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '406', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'base.node': {
            'Meta': {'unique_together': "((u'address', u'port'),)", 'object_name': 'Node'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'nodes'", 'on_delete': 'models.PROTECT', 'to': u"orm['base.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'2'", 'max_length': '2'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 8, 0, 0)', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['base']