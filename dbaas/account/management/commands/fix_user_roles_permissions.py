# encoding: utf-8
# from datetime import datetime
import sys
import traceback
import logging
from sets import Set
from django.contrib.auth.models import User, Group, Permission
from django.core.management.base import BaseCommand


only_print_errors = True

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = u'Fix user roles permissions'
    
    #dba has all permissions in role_reguler
    groups_roles = {'role_dba': [u'view_host', u'change_enginetype', u'delete_planattribute', u'add_enginetype', 
                                u'view_databaseinfra', u'change_databaseinfra', u'change_host', 
                                u'delete_auditrequest', u'change_auditchange', u'add_instance', 
                                u'can_manage_quarantine_databases', u'add_planattribute', 
                                u'delete_plan', u'add_databaseinfra', u'view_planattribute', 
                                u'change_planattribute', u'change_auditrequest', u'delete_host', 
                                u'add_host', u'change_plan', u'view_plan', u'change_audit', u'delete_audit', 
                                u'add_audit', u'change_instance', u'view_engine', u'change_engine', 
                                u'delete_databaseinfra', u'add_auditchange', u'add_auditrequest',
                                u'add_group', u'change_group', u'delete_group',
                                u'add_user', u'change_user', u'delete_user',
                                u'view_enginetype', u'delete_auditchange', u'add_engine', 
                                u'delete_instance', u'delete_enginetype', u'view_instance', u'delete_engine', u'add_plan'],
                    'role_regular': [u'add_credential', u'change_credential', u'delete_credential', u'view_credential', 
                                    u'add_database', u'change_database', u'delete_database', u'view_database', 
                                    u'add_project', u'change_project', u'delete_project', u'view_project']}

    def handle(self, *args, **options):

        #print "groups_roles: %s" % Command.groups_roles
        role_dba = Group.objects.get_or_create(name="role_dba")[0]
        role_regular = Group.objects.get_or_create(name="role_regular")[0]

        #clean permissions
        self.remove_permissions(group=role_dba)
        self.remove_permissions(group=role_regular)

        #role_regular
        codenames = Command.groups_roles['role_regular']
        permissions_regular = Permission.objects.filter(codename__in=codenames)
        self.add_permissions(group=role_regular, permissions=permissions_regular)
        
        #role_dba
        codenames = codenames + Command.groups_roles['role_dba']
        permissions_dba = Permission.objects.filter(codename__in=codenames)
        self.add_permissions(group=role_dba, permissions=permissions_dba)

    def remove_permissions(self, group=None):
        print "removing permissions for group %s" % group
        [group.permissions.remove(permission) for permission in group.permissions.all()]
        print "*" *50

    def add_permissions(self, group=None, permissions=None):
        print "adding permissions %s to group %s" % (permissions, group)
        [group.permissions.add(permission) for permission in permissions]
        print "*" *50