# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from physical.models import Instance, Host, DatabaseInfra, Engine, EngineType, Plan, PlanAttribute
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Migration(SchemaMigration):

    def forwards(self, orm):
        content_type = ContentType.objects.get_for_model(Instance)
        permission = Permission.objects.create(codename='view_instance',
                                               name='Can view instances',
                                               content_type=content_type)


        content_type = ContentType.objects.get_for_model(Host)
        permission = Permission.objects.create(codename='view_host',
                                               name='Can view hosts',
                                               content_type=content_type)

        content_type = ContentType.objects.get_for_model(DatabaseInfra)
        permission = Permission.objects.create(codename='physical.view_databaseinfra',
                                               name='Can view database infras',
                                               content_type=content_type)

        content_type = ContentType.objects.get_for_model(Engine)
        permission = Permission.objects.create(codename='view_engine',
                                               name='Can view engines',
                                               content_type=content_type)


        content_type = ContentType.objects.get_for_model(EngineType)
        permission = Permission.objects.create(codename='view_enginetype',
                                               name='Can view engine types',
                                               content_type=content_type)

        content_type = ContentType.objects.get_for_model(Plan)
        permission = Permission.objects.create(codename='view_plan',
                                               name='Can view plans',
                                               content_type=content_type)

        content_type = ContentType.objects.get_for_model(PlanAttribute)
        permission = Permission.objects.create(codename='view_planattribute',
                                               name='Can view plan attributes',
                                               content_type=content_type)

    def backwards(self, orm):
        content_type = ContentType.objects.get_for_model(Instance)
        permission = Permission.objects.get(codename='view_instance',
                                               content_type=content_type)
        permission.delete()

        content_type = ContentType.objects.get_for_model(Host)
        permission = Permission.objects.get(codename='view_host',
                                               content_type=content_type)
        permission.delete()

        content_type = ContentType.objects.get_for_model(DatabaseInfra)
        permission = Permission.objects.get(codename='view_databaseinfra',
                                               content_type=content_type)
        permission.delete()

        content_type = ContentType.objects.get_for_model(Engine)
        permission = Permission.objects.get(codename='view_engine',
                                               content_type=content_type)
        permission.delete()

        content_type = ContentType.objects.get_for_model(EngineType)
        permission = Permission.objects.get(codename='view_enginetype',
                                               content_type=content_type)
        permission.delete()

        content_type = ContentType.objects.get_for_model(Plan)
        permission = Permission.objects.get(codename='view_plan',
                                               content_type=content_type)
        permission.delete()


        content_type = ContentType.objects.get_for_model(PlanAttribute)
        permission = Permission.objects.get(codename='view_planattribute',
                                               content_type=content_type)
        permission.delete()

    models = {
        u'physical.databaseinfra': {
            'Meta': {'object_name': 'DatabaseInfra'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'engine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'databaseinfras'", 'on_delete': 'models.PROTECT', 'to': u"orm['physical.Engine']"}),
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