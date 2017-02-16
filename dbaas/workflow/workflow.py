# -*- coding: utf-8 -*-
import logging
import time
from util import full_stack
from django.utils.module_loading import import_by_path
from exceptions.error_codes import DBAAS_0001

LOG = logging.getLogger(__name__)


def start_workflow(workflow_dict, task=None):
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


def start_workflow_ha(workflow_dict, task=None):
    if 'steps' not in workflow_dict:
        return False

    init_workflow_vars(workflow_dict)

    try:
        for instance in workflow_dict['instances']:
            workflow_dict['instance_step_counter'] = 0
            task.update_details(
                persist=True,
                details='\n>> Starting steps for VM {}:'.format(instance.hostname)
            )
            workflow_dict['instance'] = instance
            workflow_dict['host'] = instance.hostname

            if workflow_dict['databaseinfra'].plan.is_ha and workflow_dict['driver'].check_instance_is_master(instance):
                LOG.info("Waiting 60s to check continue...")
                time.sleep(60)
                workflow_dict['driver'].check_replication_and_switch(instance)
                LOG.info("Waiting 60s to check continue...")
                time.sleep(60)

            for step in workflow_dict['steps']:
                workflow_dict['global_step_counter'] += 1
                workflow_dict['instance_step_counter'] += 1
                execute(step, workflow_dict, False, task)

            workflow_dict['completed_instances'].append(instance)

        workflow_dict['created'] = True
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

        workflow_dict['steps_until_stopped'] = workflow_dict[
            'steps'][:workflow_dict['instance_step_counter']]

        stop_workflow_ha(workflow_dict, task)

        return False


def stop_workflow_ha(workflow_dict, task=None):
    LOG.info("Running undo...")

    if 'steps' not in workflow_dict:
        return False

    init_rollback_vars(workflow_dict)

    try:
        for step in workflow_dict['steps_until_stopped'][::-1]:
            execute(step, workflow_dict, True, task)
            workflow_dict['global_step_counter'] -= 1

        for instance in workflow_dict['completed_instances']:
            workflow_dict['instance'] = instance
            workflow_dict['host'] = instance.hostname

            if workflow_dict['databaseinfra'].plan.is_ha and workflow_dict['driver'].check_instance_is_master(instance):
                LOG.info("Waiting 60s to check continue...")
                time.sleep(60)
                workflow_dict['driver'].check_replication_and_switch(instance)
                LOG.info("Waiting 60s to check continue...")
                time.sleep(60)

            for step in workflow_dict['steps'][::-1]:
                execute(step, workflow_dict, True, task)
                workflow_dict['global_step_counter'] -= 1

        return True
    except Exception as e:
        LOG.info("Exception: {}".format(e))

        if not workflow_dict['exceptions']['error_codes'] or not workflow_dict['exceptions']['traceback']:
            traceback = full_stack()
            workflow_dict['exceptions']['error_codes'].append(DBAAS_0001)
            workflow_dict['exceptions']['traceback'].append(traceback)

        LOG.warn("\n".join(
            ": ".join(error) for error in workflow_dict['exceptions']['error_codes']
        ))
        LOG.warn("\nException Traceback\n".join(
            workflow_dict['exceptions']['traceback'])
        )

        return False


def init_workflow_vars(workflow_dict):
    workflow_dict['driver'] = workflow_dict['databaseinfra'].get_driver()
    workflow_dict['instance_step_counter'] = 0
    workflow_dict['global_step_counter'] = 0
    workflow_dict['completed_instances'] = []
    workflow_dict['created'] = False

    workflow_dict['msgs'] = []
    workflow_dict['status'] = 0

    workflow_dict['exceptions'] = {}
    workflow_dict['exceptions']['traceback'] = []
    workflow_dict['exceptions']['error_codes'] = []

    workflow_dict['total_steps'] = \
        len(workflow_dict['steps']) * len(workflow_dict['instances'])


def init_rollback_vars(workflow_dict):
    workflow_dict['driver'] = workflow_dict['databaseinfra'].get_driver()
    if 'exceptions' not in workflow_dict:
        workflow_dict['exceptions'] = {}
        workflow_dict['exceptions']['traceback'] = []
        workflow_dict['exceptions']['error_codes'] = []

    if 'steps_until_stopped' not in workflow_dict:
        workflow_dict['steps_until_stopped'] = workflow_dict['steps']
        workflow_dict['completed_instances'] = []
        workflow_dict['global_step_counter'] = \
            len(workflow_dict['steps']) * len(workflow_dict['instances'])

    workflow_dict['msgs'] = []

    workflow_dict['total_steps'] = \
        len(workflow_dict['steps'])*\
        len(workflow_dict['completed_instances'])+\
        len(workflow_dict['steps_until_stopped'])


def execute(step, workflow_dict, is_rollback, task):
    my_class = import_by_path(step)
    my_instance = my_class()

    time_now = str(time.strftime("%m/%d/%Y %H:%M:%S"))

    kind_of = "Rollback " if is_rollback else ""

    msg = "\n%s - %sStep %i of %i - %s" % (
        time_now,
        kind_of,
        workflow_dict['global_step_counter'],
        workflow_dict['total_steps'],
        str(my_instance)
    )

    LOG.info(msg)

    if task:
        workflow_dict['msgs'].append(msg)
        task.update_details(persist=True, details=msg)

    if is_rollback:
        my_instance.undo(workflow_dict)
    else:
        if not my_instance.do(workflow_dict):
            workflow_dict['status'] = 0
            raise Exception(
                "We caught an error while executing the steps...")
        workflow_dict['status'] = 1

    if task:
        task.update_details(persist=True, details="DONE!")


def steps_for_instances(
        list_of_groups_of_steps, instances, task, step_counter_method=None, since_step=0
):
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

                    task.add_step(step_current, steps_total, str(step_instance))

                    if step_current < since_step:
                        task.update_details("SKIPPED!", persist=True)
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

    return True
