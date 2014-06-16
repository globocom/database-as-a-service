from django.utils.module_loading import import_by_path


def start_workflow(workflow_dict):
	try :
		step_counter = 0 

		for step in workflow_dict['steps']:
			step_counter+=1
			my_class = import_by_path(step)
			my_instance = my_class()

			if my_instance.do(workflow_dict)!=True:
				raise Exception
			
	except Exception, e:
		workflow_dict['steps'] = workflow_dict['steps'][:step_counter]
		stop_workflow(workflow_dict)


def stop_workflow(workflow_dict):

	for step in workflow_dict['steps'][::-1]:
		my_class = import_by_path(step)
		my_instance = my_class()
		my_instance.undo(workflow_dict)
