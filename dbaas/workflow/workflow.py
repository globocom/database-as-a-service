# -*- coding: utf-8 -*-
import logging
import time
from util import full_stack
from django.utils.module_loading import import_by_path
from exceptions.error_codes import DBAAS_0001
from logical.models import Database
from physical.models import DatabaseInfra, Instance
from system.models import Configuration

LOG = logging.getLogger(__name__)


def _get_databases(params):
    databases = set()
    for param in params.values():
        if isinstance(param, Database):
            databases.add(param)

        if isinstance(param, list):
            for item in param:
                if isinstance(item, Instance):
                    database = item.databaseinfra.databases.first()
                    if database:
                        databases.add(database)

        if isinstance(param, DatabaseInfra):
            database = param.databases.first()
            if database:
                databases.add(database)

    return databases


def _lock_databases(params, task):
    if not task:
        return True

    databases = _get_databases(params)
    databases_pinned = []
    for database in databases:
        if not database.pin_task(task):
            task.error_in_lock(database)
            for database in databases_pinned:
                database.finish_task()
            return False
        databases_pinned.append(database)

    return True


def _unlock_databases(params, task):
    if not task:
        return

    databases = _get_databases(params)
    for database in databases:
        database.finish_task()


def start_workflow(workflow_dict, task=None):
    if not _lock_databases(workflow_dict, task):
        return False

    workflow_dict['database_pinned'] = True

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

        _unlock_databases(workflow_dict, task)
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
    if 'database_pinned' not in workflow_dict:
        if not _lock_databases(workflow_dict, task):
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

        _unlock_databases(workflow_dict, task)
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

    if steps_for_instances(group_of_steps, instances, task, update_step):
        return True

    rollback_for_instances(
        group_of_steps, instances, task,
        steps_for_instances_with_rollback.current_step
    )
    unlock_databases_for(instances)
    return False


def steps_for_instances(
        list_of_groups_of_steps, instances, task, step_counter_method=None,
        since_step=0, undo=False
):
    is_retry = since_step > 0
    success, locked_databases = lock_databases_for(instances, task, is_retry)
    if not success:
        return False

    steps_total = total_of_steps(list_of_groups_of_steps, instances)
    step_current = 0

    step_header_for(task, instances, since_step)

    if undo:
        list_of_groups_of_steps.reverse()

    step_max_retry = Configuration.get_by_name_as_int('max_step_retry', 0) + 1

    for count, group_of_steps in enumerate(list_of_groups_of_steps, start=1):
        task.add_detail('Starting group of steps {} of {} - {}'.format(
            count, len(list_of_groups_of_steps), group_of_steps.keys()[0])
        )

        steps = list(group_of_steps.items()[0][1])
        if undo:
            steps.reverse()

        for instance in instances:
            task.add_detail('Instance: {}'.format(instance))
            for step in steps:
                step_current += 1

                if step_counter_method:
                    step_counter_method(step_current)

                try:
                    step_class = import_by_path(step)
                    step_instance = step_class(instance)
                    str_step_instance = str(step_instance)
                    if undo:
                        str_step_instance = 'Rollback ' + str_step_instance

                    task.add_step(step_current, steps_total, str_step_instance)

                    if step_current < since_step or not step_instance.can_run:
                        task.update_details("SKIPPED!", persist=True)
                        continue
                except Exception as e:
                    task.update_details("FAILED!", persist=True)
                    task.add_detail(str(e))
                    task.add_detail(full_stack())
                    return False

                for retry in range(1, 1 + step_max_retry):
                    try:
                        if undo:
                            step_instance.undo()
                        else:
                            step_instance.do()
                    except Exception as e:
                        if retry == step_max_retry:
                            task.update_details("FAILED!", persist=True)
                            task.add_detail(str(e))
                            task.add_detail(full_stack())
                            return False
                        else:
                            task.update_details(
                                "FAILED! Retrying ({}/{})...".format(
                                    retry, step_max_retry - 1
                                )
                            )
                            LOG.debug(str(e))
                            LOG.debug(full_stack())
                            time.sleep(3 * retry)
                            task.add_step(
                                step_current, steps_total, str_step_instance
                            )
                    else:
                        task.update_details("SUCCESS!", persist=True)
                        break

        task.add_detail('Ending group of steps: {} of {}\n'.format(
            count, len(list_of_groups_of_steps))
        )

    unlock_databases(locked_databases)
    return True


def rollback_for_instances(group_of_steps, instances, task, from_step):
    if len(group_of_steps) > 1:
        task.add_detail('Rollback is implemented only for one group of steps!')
        return False

    steps = group_of_steps[0].items()[0][1]
    i = 0
    for instance in instances:
        instance_current_step = 0
        for _ in steps:
            i += 1
            instance_current_step += 1
            if i == from_step:
                break
        if i == from_step:
            break

    task.add_detail('Starting undo for instance {}'.format(instance))

    undo_step_current = len(steps)
    for step in reversed(steps):
        try:
            step_class = import_by_path(step)
            step_instance = step_class(instance)

            task.add_step(
                undo_step_current, len(steps), 'Rollback ' + str(step_instance)
            )

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


def databases_for(instances):
    databases = set()
    for instance in instances or []:
        database = instance.databaseinfra.databases.first()
        if database:
            databases.add(database)
    return databases


def lock_databases_for(instances, task, is_retry):
    databases = databases_for(instances)
    for database in databases:
        databases_locked = []

        if not database.update_task(task):
            task.error_in_lock(database)

            if not is_retry:
                unlock_databases(databases_locked)
            return False, databases

        databases_locked.append(database)

    return True, databases


def unlock_databases(databases):
    for database in databases:
        database.finish_task()


def unlock_databases_for(instances):
    databases = databases_for(instances)
    unlock_databases(databases)


def total_of_steps(groups, instances):
    total = 0
    for group in groups:
        total += len(group.values()[0])

    return total * len(instances)


def step_header_for(task, instances, since_step=None):
    task.add_detail('Instances: {}'.format(len(instances)))
    for instance in instances:
        task.add_detail('{}'.format(instance), level=2)

    task.add_detail('')
    if since_step:
        task.add_detail('Skipping until step {}\n'.format(since_step))


def rollback_for_instances_full(
        groups, instances, task, step_current_method, step_counter_method
):
    task.add_detail('\nSTARTING ROLLBACK\n')

    instances = instances or []
    current_step = step_current_method()
    steps_total = total_of_steps(groups, instances)
    since_step = (steps_total - current_step) + 1

    instances.reverse()
    result = steps_for_instances(
        groups, instances, task, step_counter_method, since_step, True
    )

    executed_steps = step_current_method()
    missing_undo_steps = steps_total - (executed_steps - 1)
    step_counter_method(missing_undo_steps)

    return result
