# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
# import mock
from django.test import TestCase
from django.conf import settings
from ..cloudstack import CloudStackClient




class CloudStackProviderTestCase(TestCase):
    """
    Tests MySQL Engine
    """

    def setUp(self):
    	self.api  = CloudStackClient(settings.CLOUD_STACK_API_URL, settings.CLOUD_STACK_API_KEY, settings.CLOUD_STACK_API_SECRET)


    def test_create_cloud_stack_instance(self):
    	self.request = { 'serviceofferingid':'5a5a6fae-73db-44d6-a05e-822ed5bd0548', 
                            'templateid': '6e94d4d0-a1d6-405c-b226-e1ce6858c97d', 
                            'zoneid': 'c70c584b-4525-4399-9918-fff690489036',
                            'networkids': '250b249b-5eb0-476a-b892-c6a6ced45aad',
                            'projectid': '0be19820-1fe2-45ea-844e-77f17e16add5'
                           }
	self.response = self.api.deployVirtualMachine(self.request)
	self.vm_id = self.request['id']
	self.request = {'id':'%s' %(self.vm_id)}
	self.assertEqual(vm_id, request['id'])

    def tearDown(self):
    	self.api.destroyVirtualMachine(self.request)