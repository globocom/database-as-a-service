# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
from rest_framework import test


class DbaaSClient(test.APIClient):

    def request(self, **kwargs):
        # Ensure that any credentials set get added to every request.
        response = super(DbaaSClient, self).request(**kwargs)
        # convert data from json using rendered content
        if response.accepted_media_type == 'application/json' and response.data:
            response.original_data = response.data
            response.data = json.loads(response.rendered_content)
        return response


class DbaaSAPITestCase(test.APITestCase):
    client_class = DbaaSClient
