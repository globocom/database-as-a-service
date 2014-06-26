# -*- coding: utf-8 -*-
from django.utils.module_loading import import_by_path
import logging

LOG = logging.getLogger(__name__)


def start_workflow(workflow_dict, task=None):
    try:
        if not 'steps' in workflow_dict:
            return False
        workflow_dict['step_counter'] = 0

        workflow_dict['msgs'] = []

        for step in workflow_dict['steps']:
            workflow_dict['step_counter'] += 1

            my_class = import_by_path(step)
            my_instance = my_class()

            LOG.info("Step %i %s " %
                     (workflow_dict['step_counter'], str(my_instance)))


            if task:
                workflow_dict['msgs'].append(str(my_instance))
                task.update_details(persist=True, details="\n".join(workflow_dict['msgs']))

            if my_instance.do(workflow_dict) != True:
                raise Exception

    except Exception, e:
        print e
        workflow_dict['steps'] = workflow_dict[
            'steps'][:workflow_dict['step_counter']]
        stop_workflow(workflow_dict)


def stop_workflow(workflow_dict):
    LOG.info("Running undo...")

    try:

        for step in workflow_dict['steps'][::-1]:

            my_class = import_by_path(step)
            my_instance = my_class()

            if 'step_counter' in workflow_dict:
                workflow_dict['step_counter'] -= 1
                LOG.info("Step %i %s " %
                        (workflow_dict['step_counter'], str(my_instance)))
            my_instance.undo(workflow_dict)

        return True
    except Exception, e:
        print e
        return False
