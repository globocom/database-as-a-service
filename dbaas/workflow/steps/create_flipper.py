# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_flipper.provider import FlipperProvider


LOG = logging.getLogger(__name__)


class CreateFlipper(BaseStep):

    def __unicode__(self):
        return "Creating Flipper"

    def do(self, workflow_dict):
        try:
            if workflow_dict['qt']==1:
                return True
            flipper = FlipperProvider()
            LOG.info("Creating Flipper...")
            flipper.create_flipper_dependencies(
                masterpairname=workflow_dict['names']['infra'],
                hostname1=workflow_dict[
                    'hosts'][0].address,
                writeip=workflow_dict[
                    'databaseinfraattr'][0].ip,
                readip=workflow_dict[
                    'databaseinfraattr'][1].ip,
                hostname2=workflow_dict[
                    'hosts'][1].address,
                environment=workflow_dict['environment'])

            return True
        except Exception, e:
            print e
            return False

    def undo(self, workflow_dict):
        try:
            if workflow_dict['qt']==1:
                return True
            LOG.info("Destroying Flipper...")
            FlipperProvider(
            ).destroy_flipper_dependencies(masterpairname=workflow_dict['databaseinfra'].name,
                                           environment=workflow_dict['environment'])

            return True
        except Exception, e:
            print e
            return False
