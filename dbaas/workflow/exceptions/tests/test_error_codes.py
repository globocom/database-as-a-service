# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from workflow.exceptions.error_codes import DBAAS_0001
from workflow.exceptions.error_codes import DBAAS_0002
from workflow.exceptions.error_codes import DBAAS_0003
from workflow.exceptions.error_codes import DBAAS_0004
from workflow.exceptions.error_codes import DBAAS_0005
from workflow.exceptions.error_codes import DBAAS_0006
from workflow.exceptions.error_codes import DBAAS_0007
from workflow.exceptions.error_codes import DBAAS_0008
from workflow.exceptions.error_codes import DBAAS_0009
from workflow.exceptions.error_codes import DBAAS_0010
from workflow.exceptions.error_codes import DBAAS_0011
from workflow.exceptions.error_codes import DBAAS_0012
from workflow.exceptions.error_codes import DBAAS_0013
from workflow.exceptions.error_codes import DBAAS_0014
from workflow.exceptions.error_codes import DBAAS_0015
from workflow.exceptions.error_codes import DBAAS_0016
from workflow.exceptions.error_codes import DBAAS_0017
from workflow.exceptions.error_codes import DBAAS_0018
from workflow.exceptions.error_codes import DBAAS_0019
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.exceptions.error_codes import DBAAS_0021
from workflow.exceptions.error_codes import DBAAS_0022
from django.test import TestCase
LOG = logging.getLogger(__name__)


class ErrorCodeTestCase(TestCase):

    def test_error_messages(self):
        self.assertEqual(DBAAS_0001, ("DBAAS_0001", "Workflow error"))
        self.assertEqual(
            DBAAS_0002, ("DBAAS_0002", "Build DatabaseInfra error"))
        self.assertEqual(DBAAS_0003, ("DBAAS_0003", "Build Database error"))
        self.assertEqual(DBAAS_0004, ("DBAAS_0004", "Check Database error"))
        self.assertEqual(DBAAS_0005, ("DBAAS_0005", "Check DNS error"))
        self.assertEqual(DBAAS_0006, ("DBAAS_0006", "Create DBMonitor error"))
        self.assertEqual(DBAAS_0007, ("DBAAS_0007", "Create DNS error"))
        self.assertEqual(DBAAS_0008, ("DBAAS_0008", "Create Flipper error"))
        self.assertEqual(DBAAS_0009, ("DBAAS_0009", "Create NFS error"))
        self.assertEqual(DBAAS_0010, ("DBAAS_0010", "Create ScondaryIP error"))
        self.assertEqual(
            DBAAS_0011, ("DBAAS_0011", "Create VirtualMachine error"))
        self.assertEqual(DBAAS_0012, ("DBAAS_0012", "Create Zabbix error"))
        self.assertEqual(
            DBAAS_0013, ("DBAAS_0013", "Initializing MYSQL Database error"))
        self.assertEqual(
            DBAAS_0014, ("DBAAS_0014", "Initializing MONGODB Database error"))
        self.assertEqual(DBAAS_0015, ("DBAAS_0015", "Resize Database error"))
        self.assertEqual(
            DBAAS_0016, ("DBAAS_0016", "Initializing REDIS Database error"))
        self.assertEqual(DBAAS_0017, ("DBAAS_0017", "Clone Database error"))
        self.assertEqual(DBAAS_0018, ("DBAAS_0018", "Create LaaS error"))
        self.assertEqual(DBAAS_0019, ("DBAAS_0019", "Checking Database Binds"))
        self.assertEqual(
            DBAAS_0020, ("DBAAS_0020", "Database Migration error"))
        self.assertEqual(DBAAS_0021, ("DBAAS_0021", "Restore Snapshot error"))
        self.assertEqual(DBAAS_0022, ("DBAAS_0022", "Volume Migration Error"))
