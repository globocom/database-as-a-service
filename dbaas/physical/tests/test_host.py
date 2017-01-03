# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError
from django.contrib import admin
from ..admin.host import HostAdmin, HostAttrNfsaasInline, HostAttrNfsaas
from ..models import Host
from .factory import HostFactory

SEARCH_FIELDS = ('hostname', 'nfsaas_host_attributes__nfsaas_path',
                 'address', 'os_description')
EDITING_READ_ONLY_FIELDS = ('nfsaas_size_kb', 'nfsaas_used_size_kb')


class HostTestCase(TestCase):

    def setUp(self):
        self.host = HostFactory(hostname='unique_localhost')
        self.admin = HostAdmin(Host, admin.sites.AdminSite())
        self.admin_nfsaas = HostAttrNfsaasInline(
            HostAttrNfsaas, admin.sites.AdminSite()
        )

    def test_create_host(self):
        host = HostFactory()
        self.assertTrue(host.id)

    def test_unique_host(self):
        another_instance = self.host
        another_instance.id = None

        self.assertRaises(IntegrityError, another_instance.save)

    def test_search_fields(self):
        self.assertEqual(SEARCH_FIELDS, self.admin.search_fields)

    def test_read_only_fields_nfsaas_editing(self):
        admin_read_only = self.admin_nfsaas.get_readonly_fields(
            request=None, obj=self.host
        )
        self.assertEqual(EDITING_READ_ONLY_FIELDS, admin_read_only)

    def test_read_only_fields_nfsaas_adding(self):
        admin_read_only = self.admin_nfsaas.get_readonly_fields(
            request=None, obj=None
        )
        self.assertNotEqual(EDITING_READ_ONLY_FIELDS, admin_read_only)
