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


class SetFeatureCompatibilityVersion40(DatabaseStep):

    def __unicode__(self):
        return "Setting Compatibility Version to 40..."

    def getFeatureCompatibilityVersion(self, client):
        parameters = client.admin.command('getParameter', '*')
        return parameters['featureCompatibilityVersion']['version']

    def do(self):

        client = self.driver.get_client(None)
        if self.getFeatureCompatibilityVersion(client) != '4.0':
            client.admin.command('setFeatureCompatibilityVersion', '4.0')
            if self.getFeatureCompatibilityVersion(client) != '4.0':
                raise EnvironmentError(
                    'Could not set featureCompatibilityVersion on {}'.format(
                        self.infra.name
                    )
                )


class SetFeatureCompatibilityVersion36(DatabaseStep):

    def __unicode__(self):
        return "Setting Compatibility Version to 36..."

    def getFeatureCompatibilityVersion(self, client):
        parameters = client.admin.command('getParameter', '*')
        return parameters['featureCompatibilityVersion']['version']

    def do(self):

        client = self.driver.get_client(None)
        if self.getFeatureCompatibilityVersion(client) != '3.6':
            client.admin.command('setFeatureCompatibilityVersion', '3.6')
            if self.getFeatureCompatibilityVersion(client) != '3.6':
                raise EnvironmentError(
                    'Could not set featureCompatibilityVersion on {}'.format(
                        self.infra.name
                    )
                )

class SetFeatureCompatibilityToNewVersion(DatabaseStep):

    def __unicode__(self):
        return "Setting Compatibility Version new version..."

    @property
    def is_valid(self):
        if self.upgrade and self.instance == self.infra.instances.all()[0]:
            return True
        return False

    @property
    def target_version(self):
        if self.upgrade:
            engine = self.upgrade.target_plan.engine
            return "{}.{}".format(engine.major_version, engine.minor_version)

    def getFeatureCompatibilityVersion(self, client):
        parameters = client.admin.command('getParameter', '*')
        return parameters['featureCompatibilityVersion']['version']

    def do(self):
        if not self.is_valid:
            return

        client = self.driver.get_client(None)
        target_version = self.target_version

        if self.getFeatureCompatibilityVersion(client) != target_version:
            client.admin.command('setFeatureCompatibilityVersion',
                target_version)
            if self.getFeatureCompatibilityVersion(client) != target_version:
                raise EnvironmentError(
                    'Could not set featureCompatibilityVersion on {}'.format(
                        self.infra.name)
                )

