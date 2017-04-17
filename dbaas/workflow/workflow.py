# -*- coding: utf-8 -*-
import logging
import time
from util import full_stack
from django.utils.module_loading import import_by_path
from exceptions.error_codes import DBAAS_0001
from logical.models import Database
from physical.models import DatabaseInfra, Instance


LOG = logging.getLogger(__name__)


def _get_database_in_params(params):
    for param in params.values():
        if isinstance(param, Database):
            return param
        elif isinstance(param, DatabaseInfra):
            return param.databases.first()
        elif isinstance(param, list):
            for item in param:
                if isinstance(item, Instance):
                    return item.databaseinfra.databases.first()


def start_workflow(workflow_dict, task=None):
    database = _get_database_in_params(workflow_dict)

    LOG.debug(workflow_dict)
    if database:
        LOG.debug("Database encontrada!!!!")
        if not database.pin_task(task):
            task.update_details("FAILED!", persist=True)
            task.add_detail(
                "Database {} is not allocated for this task.".format(
                    database.name
                )
            )
            return False
        workflow_dict['task_pinned'] = True

    try:
        if 'steps' not in workflow_dict:
            return False
        workflow_dict['step_counter'] = 0

        workflow_dict['msgs'] = []
        workflow_dict['status'] = 0
        workflow_dict['total_steps'] = len(workflow_dict['steps'])
        workflow_dict['exceptions'] = {}
        workflow_dict['exceptions']['traceback'] = []
        workflow_dict['exceptions']['error_codes'] = []

        for step in workflow_dict['steps']:
            workflow_dict['step_counter'] += 1

            my_class = import_by_path(step)
            my_instance = my_class()

            time_now = str(time.strftime("%m/%d/%Y %H:%M:%S"))

            msg = "\n%s - Step %i of %i - %s" % (
                time_now, workflow_dict['step_counter'], workflow_dict['total_steps'], str(my_instance))

            LOG.info(msg)

            if task:
                workflow_dict['msgs'].append(msg)
                task.update_details(persist=True, details=msg)

            if not my_instance.do(workflow_dict):
                workflow_dict['status'] = 0
                raise Exception(
                    "We caught an error while executing the steps...")

            workflow_dict['status'] = 1
            if task:
                task.update_details(persist=True, details="DONE!")

        workflow_dict['created'] = True

        if database:
            database.unpin_task()
        return True

    except Exception:

        if not workflow_dict['exceptions']['error_codes'] or not workflow_dict['exceptions']['traceback']:
            traceback = full_stack()
            workflow_dict['exceptions']['error_codes'].append(DBAAS_0001)
            workflow_dict['exceptions']['traceback'].append(traceback)

        LOG.warn("\n".join(": ".join(error)
                           for error in workflow_dict['exceptions']['error_codes']))
        LOG.warn("\nException Traceback\n".join(
            workflow_dict['exceptions']['traceback']))

        workflow_dict['steps'] = workflow_dict[
            'steps'][:workflow_dict['step_counter']]
        stop_workflow(workflow_dict, task)

        return False


def stop_workflow(workflow_dict, task=None):
    LOG.info("Running undo...")
    database = _get_database_in_params(workflow_dict)
    if database and 'task_pinned' not in workflow_dict:
        if not database.pin_task(task):
            task.update_details("FAILED!", persist=True)
            task.add_detail(
                "Database {} is not allocated for this task.".format(
                    database.name
                )
            )
            return False

    if 'steps' not in workflow_dict:
        return False

    if 'exceptions' not in workflow_dict:
        workflow_dict['exceptions'] = {}
        workflow_dict['exceptions']['traceback'] = []
        workflow_dict['exceptions']['error_codes'] = []

    workflow_dict['total_steps'] = len(workflow_dict['steps'])
    if 'step_counter' not in workflow_dict:
        workflow_dict['step_counter'] = len(workflow_dict['steps'])
    workflow_dict['msgs'] = []
    workflow_dict['created'] = False

    try:

        for step in workflow_dict['steps'][::-1]:

            my_class = import_by_path(step)
            my_instance = my_class()

            time_now = str(time.strftime("%m/%d/%Y %H:%M:%S"))

            msg = "\n%s - Rollback Step %i of %i - %s" % (
                time_now, workflow_dict['step_counter'], workflow_dict['total_steps'], str(my_instance))

            LOG.info(msg)

            workflow_dict['step_counter'] -= 1

            if task:
                workflow_dict['msgs'].append(msg)
                task.update_details(persist=True, details=msg)

            my_instance.undo(workflow_dict)

            if task:
                task.update_details(persist=True, details="DONE!")

        if database:
            database.unpin_task()
        return True
    except Exception as e:
        LOG.info("Exception: {}".format(e))

        if not workflow_dict['exceptions']['error_codes'] or not workflow_dict['exceptions']['traceback']:
            traceback = full_stack()
            workflow_dict['exceptions']['error_codes'].append(DBAAS_0001)
            workflow_dict['exceptions']['traceback'].append(traceback)

        LOG.warn("\n".join(": ".join(error)
                           for error in workflow_dict['exceptions']['error_codes']))
        LOG.warn("\nException Traceback\n".join(
            workflow_dict['exceptions']['traceback']))
        return False


def steps_for_instances_with_rollback(group_of_steps, instances, task):

    steps_for_instances_with_rollback.current_step = 0

    def update_step(step):
        steps_for_instances_with_rollback.current_step = step

    ret = steps_for_instances(
        list_of_groups_of_steps=group_of_steps,
        instances=instances,
        task=task,
        step_counter_method=update_step
    )

    if ret:
        return ret

    if len(group_of_steps) > 1:
        task.add_detail('Rollback is implemented only for one group of steps!')
        return False

    steps = group_of_steps[0].items()[0][1]
    i = 0
    for instance in instances:
        instance_current_step = 0
        for step in steps:
            i += 1
            instance_current_step += 1
            if i == steps_for_instances_with_rollback.current_step:
                break
        if i == steps_for_instances_with_rollback.current_step:
            break

    task.add_detail('Starting undo for instance {}'.format(instance))

    undo_step_current = len(steps)
    for step in reversed(steps):

        try:
            step_class = import_by_path(step)
            step_instance = step_class(instance)

            task.add_step(undo_step_current, len(steps), 'Rollback ' + str(step_instance))

            if instance_current_step < undo_step_current:
                task.update_details("SKIPPED!", persist=True)
            else:
                step_instance.undo()
                task.update_details("SUCCESS!", persist=True)

        except Exception as e:
            task.update_details("FAILED!", persist=True)
            task.add_detail(str(e))
            task.add_detail(full_stack())

        finally:
            undo_step_current -= 1

    databases = set()
    for instance in instances:
        databases.add(instance.databaseinfra.databases.first())

    for database in databases:
        database.unpin_task()

    return ret


def steps_for_instances(
        list_of_groups_of_steps, instances, task, step_counter_method=None,
        since_step=0, undo=False
):
    databases = set()
    for instance in instances:
        databases.add(instance.databaseinfra.databases.first())

    for database in databases:
        if since_step == 0:
            if not database.pin_task(task):
                task.update_details("FAILED!", persist=True)
                task.add_detail(
                    "Database {} is not allocated for this task.".format(
                        database.name
                    )
                )
                return False
        else:
            database.update_task(task)

    steps_total = 0
    for group_of_steps in list_of_groups_of_steps:
        steps_total += len(group_of_steps.items()[0][1])

    steps_total = steps_total * len(instances)
    step_current = 0

    task.add_detail('Instances: {}'.format(len(instances)))
    for instance in instances:
        task.add_detail('{}'.format(instance), level=2)
    task.add_detail('')

    if since_step:
        task.add_detail('Skipping until step {}\n'.format(since_step))

    for count, group_of_steps in enumerate(list_of_groups_of_steps, start=1):
        task.add_detail('Starting group of steps {} of {} - {}'.format(
            count, len(list_of_groups_of_steps), group_of_steps.keys()[0])
        )
        steps = group_of_steps.items()[0][1]
        for instance in instances:
            task.add_detail('Instance: {}'.format(instance))
            for step in steps:
                step_current += 1

                if step_counter_method:
                    step_counter_method(step_current)

                try:
                    step_class = import_by_path(step)
                    step_instance = step_class(instance)

                    if undo:
                        str_step_instance = 'Rollback ' + str(step_instance)
                    else:
                        str_step_instance = str(step_instance)
                    task.add_step(step_current, steps_total, str_step_instance)

                    if step_current < since_step:
                        task.update_details("SKIPPED!", persist=True)
                    else:
                        if undo:
                            step_instance.undo()
                        else:
                            step_instance.do()
                        task.update_details("SUCCESS!", persist=True)

                except Exception as e:
                    task.update_details("FAILED!", persist=True)
                    task.add_detail(str(e))
                    task.add_detail(full_stack())
                    return False

        task.add_detail('Ending group of steps: {} of {}\n'.format(
            count, len(list_of_groups_of_steps))
        )

    for database in databases:
        database.unpin_task()

    return True
