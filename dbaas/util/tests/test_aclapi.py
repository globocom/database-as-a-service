from unittest import TestCase
from mock import patch, PropertyMock, MagicMock
from util.aclapi import AddACLAccess
from collections import namedtuple


FAKE_CREDENTIAL = namedtuple('FakeCredential', 'endpoint user password')


class BaseACLTestCase(TestCase):
    def setUp(self):
        self.sources = ["1.1.1.1/27", "2.2.2.2/27"]
        self.destinations = ["10.10.10.10/20", "11.11.11.11/20"]
        self.default_port = 999
        self.sources_with_port = [("1.1.1.1/27", 111), ("2.2.2.2/27", 222)]
        self.fake_env = 'fake_env'


class ParseSourceTestCase(BaseACLTestCase):
    def setUp(self):
        super(ParseSourceTestCase, self).setUp()
        self.client = AddACLAccess(
            self.fake_env,
            self.sources,
            self.destinations,
            self.default_port
        )

    def test_source_port_none(self):
        source, port = self.client._parse_source("4.4.4.4/27")

        self.assertEqual(source, "4.4.4.4/27")
        self.assertEqual(port, None)

    def test_source_with_specific_port(self):
        source, port = self.client._parse_source(("4.4.4.4/27", 1234))

        self.assertEqual(source, "4.4.4.4/27")
        self.assertEqual(port, 1234)


class MakePayloadTestCase(BaseACLTestCase):
    def setUp(self):
        super(MakePayloadTestCase, self).setUp()
        self.client = AddACLAccess(
            self.fake_env,
            self.sources,
            self.destinations,
            self.default_port
        )

    def test_one_destination_default_port(self):
        self.client.destinations = self.destinations[:1]
        payload = self.client._make_payload("4.4.4.4/27")

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": "4.4.4.4/27",
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }]
        }

        self.assertDictEqual(payload, expected_payload)

    def test_multiple_destination_default_port(self):
        payload = self.client._make_payload("4.4.4.4/27")

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": "4.4.4.4/27",
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }, {
                "action": "permit",
                "protocol": "tcp",
                "source": "4.4.4.4/27",
                "destination": self.destinations[1],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }]
        }

        self.assertDictEqual(payload, expected_payload)

    def test_one_destination_specific_port(self):
        self.client.destinations = self.destinations[:1]
        payload = self.client._make_payload("4.4.4.4/27", 1234)

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": "4.4.4.4/27",
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": "1234"
                }
            }]
        }

        self.assertDictEqual(payload, expected_payload)

    def test_multiple_destination_specific_port(self):
        payload = self.client._make_payload("4.4.4.4/27", 1234)

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": "4.4.4.4/27",
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": "1234"
                }
            }, {
                "action": "permit",
                "protocol": "tcp",
                "source": "4.4.4.4/27",
                "destination": self.destinations[1],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": "1234"
                }
            }]
        }

        self.assertDictEqual(payload, expected_payload)

    def test_one_destination_no_port(self):
        self.client.destinations = self.destinations[:1]
        self.client.default_port = None
        payload = self.client._make_payload("4.4.4.4/27")

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "ip",
                "source": "4.4.4.4/27",
                "destination": self.destinations[0]
            }]
        }

        self.assertDictEqual(payload, expected_payload)

    def test_multiple_destination_no_port(self):
        self.client.default_port = None
        payload = self.client._make_payload("4.4.4.4/27")

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "ip",
                "source": "4.4.4.4/27",
                "destination": self.destinations[0],
            }, {
                "action": "permit",
                "protocol": "ip",
                "source": "4.4.4.4/27",
                "destination": self.destinations[1],
            }]
        }

        self.assertDictEqual(payload, expected_payload)


@patch('util.aclapi.AddACLAccess.credential',
       new=PropertyMock(
           return_value=FAKE_CREDENTIAL(
               'fake_endpoint/', 'user', 'pass'
           )
       ))
@patch('util.aclapi.requests.put')
@patch('util.aclapi.AddACLAccess._run_job')
class CreateACLTestCase(BaseACLTestCase):

    def test_one_source_execute_job(self, mock_run_job, mock_put):
        mock_json = MagicMock(
            return_value={
                'id': 'fake_acl_id', 'jobs': ['fake_job_id']
            }
        )
        mock_put.return_value = namedtuple(
            'FakeResp', 'ok status_code content json'
        )(True, 200, '', mock_json)
        client = AddACLAccess(
            self.fake_env,
            self.sources[:1],
            self.destinations[:1],
            self.default_port
        )
        client.create_acl()

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": self.sources[0],
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }]
        }
        self.assertTrue(mock_put.called)
        self.assertEqual(mock_put.call_count, 1)
        put_args = mock_put.call_args
        expected_endpoint = 'fake_endpoint/api/ipv4/acl/1.1.1.1/27'
        self._validate_call(put_args, expected_payload, expected_endpoint)
        self.assertTrue(mock_run_job.called)

    def test_one_source_without_execute_job(self, mock_run_job, mock_put):
        client = AddACLAccess(
            self.fake_env,
            self.sources[:1],
            self.destinations[:1],
            self.default_port
        )
        client.create_acl(execute_job=False)

        expected_payload = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": self.sources[0],
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }]
        }
        self.assertTrue(mock_put.called)
        self.assertEqual(mock_put.call_count, 1)
        put_args = mock_put.call_args
        expected_endpoint = 'fake_endpoint/api/ipv4/acl/1.1.1.1/27'
        self._validate_call(put_args, expected_payload, expected_endpoint)
        self.assertFalse(mock_run_job.called)

    def _validate_call(self, call_args, expected_payload, expected_endpoint):
        self.assertEqual(call_args[0][0], expected_endpoint)
        self.assertDictEqual(call_args[1]['json'], expected_payload)
        self.assertEqual(call_args[1]['auth'], ('user', 'pass'))

    def test_multi_sources_multi_destinations(self, mock_run_job, mock_put):
        client = AddACLAccess(
            self.fake_env,
            self.sources,
            self.destinations,
            self.default_port
        )
        client.create_acl()

        expected_payload_first_call = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": self.sources[0],
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }, {
                "action": "permit",
                "protocol": "tcp",
                "source": self.sources[0],
                "destination": self.destinations[1],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }]
        }
        expected_payload_second_call = {
            "kind": "object#acl",
            "rules": [{
                "action": "permit",
                "protocol": "tcp",
                "source": self.sources[1],
                "destination": self.destinations[0],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }, {
                "action": "permit",
                "protocol": "tcp",
                "source": self.sources[1],
                "destination": self.destinations[1],
                "l4-options": {
                    "dest-port-op": "eq",
                    "dest-port-start": str(self.default_port)
                }
            }]
        }
        self.assertTrue(mock_put.called)
        self.assertEqual(mock_put.call_count, 2)
        put_args_first, put_args_second = mock_put.call_args_list
        expected_endpoint = 'fake_endpoint/api/ipv4/acl/1.1.1.1/27'
        self._validate_call(
            put_args_first, expected_payload_first_call, expected_endpoint
        )
        expected_endpoint = 'fake_endpoint/api/ipv4/acl/2.2.2.2/27'
        self._validate_call(
            put_args_second, expected_payload_second_call, expected_endpoint
        )

    @patch('util.aclapi.LOG.info')
    def test_resp_ok(self, mock_info, mock_run_job, mock_put):
        mock_put.return_value = namedtuple(
            'FakeResp', 'ok status_code content'
        )(True, 200, '')
        client = AddACLAccess(
            self.fake_env,
            self.sources[:1],
            self.destinations[:1],
            self.default_port
        )
        client.create_acl(execute_job=False)
        self.assertIn("SUCCESS!!", mock_info.call_args[0][0])

    @patch('util.aclapi.LOG.error')
    def test_resp_not_ok(self, mock_error, mock_run_job, mock_put):
        mock_put.return_value = namedtuple(
            'FakeResp', 'ok status_code content'
        )(False, 400, 'Some error')
        client = AddACLAccess(
            self.fake_env,
            self.sources[:1],
            self.destinations[:1],
            self.default_port
        )
        with self.assertRaises(Exception):
            client.create_acl(execute_job=False)
        self.assertTrue(mock_error.called)
        self.assertIn(
            'FAIL for payload',
            mock_error.call_args[0][0]
        )
