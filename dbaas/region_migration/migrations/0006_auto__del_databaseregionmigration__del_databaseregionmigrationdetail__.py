# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'DatabaseRegionMigrationDetail', fields ['database_region_migration', 'step', 'scheduled_for']
        db.delete_unique(u'region_migration_databaseregionmigrationdetail', ['database_region_migration_id', 'step', 'scheduled_for'])

        # Deleting model 'DatabaseRegionMigration'
        db.delete_table(u'region_migration_databaseregionmigration')

        # Deleting model 'DatabaseRegionMigrationDetail'
        db.delete_table(u'region_migration_databaseregionmigrationdetail')


    def backwards(self, orm):
        # Adding model 'DatabaseRegionMigration'
        db.create_table(u'region_migration_databaseregionmigration', (
            ('database', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logical.Database'], unique=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('current_step', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'region_migration', ['DatabaseRegionMigration'])

        # Adding model 'DatabaseRegionMigrationDetail'
        db.create_table(u'region_migration_databaseregionmigrationdetail', (
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('is_migration_up', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('finished_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('scheduled_for', self.gf('django.db.models.fields.DateTimeField')()),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('step', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('celery_task_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('started_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('log', self.gf('django.db.models.fields.TextField')()),
            ('revoked_by', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('database_region_migration', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'details', to=orm['region_migration.DatabaseRegionMigration'])),
        ))
        db.send_create_signal(u'region_migration', ['DatabaseRegionMigrationDetail'])

        # Adding unique constraint on 'DatabaseRegionMigrationDetail', fields ['database_region_migration', 'step', 'scheduled_for']
        db.create_unique(u'region_migration_databaseregionmigrationdetail', ['database_region_migration_id', 'step', 'scheduled_for'])


    models = {
        
    }

    complete_apps = ['region_migration']