from django.test import TestCase


class UrlTest(TestCase):

    def test_access_emergency_contacts_url(self):
        response = self.client.get('/account/team_contacts/{}'.format(01234))
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_emergency_contacts_url_invalid_parameter(self):
        response = self.client.get('/account/team_contacts/abcde')
        self.assertEqual(response.status_code, 301)
