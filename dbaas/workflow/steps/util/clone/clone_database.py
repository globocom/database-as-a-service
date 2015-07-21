# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import call_script
from django.conf import settings
from drivers import factory_for
from notification.util import get_clone_args
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0017

LOG = logging.getLogger(__name__)


class CloneDatabase(BaseStep):

    def __unicode__(self):
        return "Replicating database data..."

    def do(self, workflow_dict):
        try:

            if 'databaseinfra' not in workflow_dict \
                    or 'clone' not in workflow_dict:
                return False

            args = get_clone_args(
                workflow_dict['clone'], workflow_dict['database'])
            script_name = factory_for(
                workflow_dict['clone'].databaseinfra).clone()

            return_code, output = call_script(
                script_name, working_dir=settings.SCRIPTS_PATH, args=args, split_lines=False,)

            LOG.info("Script Output: {}".format(output))
            LOG.info("Return code: {}".format(return_code))

            if return_code != 0:
                workflow_dict['exceptions']['traceback'].append(output)
                return False

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0017)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Nothing to do here...")
        return True
