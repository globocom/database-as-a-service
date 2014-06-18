# -*- coding: utf-8 -*-
from django.utils.module_loading import import_by_path
from notification.models import TaskHistory
import logging

LOG = logging.getLogger(__name__)

def start_workflow(workflow_dict, task=None):
	try :
		if not 'steps' in workflow_dict:
		    return False
		workflow_dict['step_counter'] = 0

		for step in workflow_dict['steps']:
			workflow_dict['step_counter']+=1

			LOG.info("Step %s number %i" % (step, workflow_dict['step_counter']))

			my_class = import_by_path(step)
			my_instance = my_class()

			if task:
			    task.update_details(persist=True, details=str(my_instance))

			if my_instance.do(workflow_dict)!=True:
			    raise Exception

	except Exception, e:
		print e
		workflow_dict['steps'] = workflow_dict['steps'][:workflow_dict['step_counter']]
		stop_workflow(workflow_dict)


def stop_workflow(workflow_dict):

	for step in workflow_dict['steps'][::-1]:
		my_class = import_by_path(step)
		my_instance = my_class()
		my_instance.undo(workflow_dict)
