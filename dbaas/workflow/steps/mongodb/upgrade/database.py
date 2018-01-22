# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.database import DatabaseStep

LOG = logging.getLogger(__name__)


class SetFeatureCompatibilityVersion34(DatabaseStep):

    def __unicode__(self):
        return "Setting Compatibility Version to 34..."

    def getFeatureCompatibilityVersion(self, client):
        parameters = client.admin.command('getParameter', '*')
        return parameters['featureCompatibilityVersion']

    def do(self):

        client = self.driver.get_client(None)
        if self.getFeatureCompatibilityVersion(client) != '3.4':
            client.admin.command('setFeatureCompatibilityVersion', '3.4')
            if self.getFeatureCompatibilityVersion(client) != '3.4':
                raise EnvironmentError(
                    'Could not set featureCompatibilityVersion on {}'.format(
                        self.infra.name
                    )
                )
