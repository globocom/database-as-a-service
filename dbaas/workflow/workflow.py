# -*- coding: utf-8 -*-
from django.utils.module_loading import import_by_path
import logging

LOG = logging.getLogger(__name__)


def start_workflow(workflow_dict, task=None):
    try:
        if not 'steps' in workflow_dict:
            return False
        workflow_dict['step_counter'] = 0

        for step in workflow_dict['steps']:
            workflow_dict['step_counter'] += 1

            my_class = import_by_path(step)
            my_instance = my_class()

            LOG.info("Step %i %s " %
                     (workflow_dict['step_counter'], str(my_instance)))

            if task:
                task.update_details(persist=True, details=str(my_instance))

            if my_instance.do(workflow_dict) != True:
                raise Exception

    except Exception, e:
        print e
        workflow_dict['steps'] = workflow_dict[
            'steps'][:workflow_dict['step_counter']]
        stop_workflow(workflow_dict)


def stop_workflow(workflow_dict):
    LOG.info("Running undo...")

    for step in workflow_dict['steps'][::-1]:
        workflow_dict['step_counter'] -= 1
        my_class = import_by_path(step)
        my_instance = my_class()

        LOG.info("Step %i %s " %
                (workflow_dict['step_counter'], str(my_instance)))
        my_instance.undo(workflow_dict)
