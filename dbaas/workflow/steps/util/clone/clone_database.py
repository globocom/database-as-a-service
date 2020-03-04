# -*- coding: utf-8 -*-
import logging
from util import call_script
from django.conf import settings
from drivers import factory_for
from notification.util import get_clone_args
from workflow.steps.util.base import BaseInstanceStep

LOG = logging.getLogger(__name__)


class CloneDatabaseData(BaseInstanceStep):

    def __unicode__(self):
        return "Replicating database data..."

    def do(self):

        if not self.is_first_instance:
            return
        try:
            args = get_clone_args(
                self.step_manager.origin_database, self.database)
            script_name = factory_for(self.infra).clone()

            return_code, output = call_script(
                script_name, working_dir=settings.SCRIPTS_PATH,
                args=args, split_lines=False
            )

            LOG.info("Script Output: {}".format(output))
            LOG.info("Return code: {}".format(return_code))

            if return_code != 0:
                raise Exception(output)
                return False

            return True
        except Exception as err:
            raise Exception(err)

            return False

    def undo(self):
        pass
