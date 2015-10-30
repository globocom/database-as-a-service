# -*- coding: utf-8 -*-
from dbaas_cloudstack.models import DatabaseInfraOffering


def database_can_not_be_resized(database, execution_plan):
    response = False
    model_name, field = parse_model_field(execution_plan.field_to_check_value)
    field_value = get_field_value(model_name, field, database)

    if field_value <= execution_plan.minimum_value:
        response = True

    return response


def get_field_value(model_name, field, database):
    response = 0
    if model_name == 'offering':
        response = get_service_offering(database, field)
    return response


def parse_model_field(model_field_str):
    return model_field_str.split('.')


def get_service_offering(database, field):
    infra_offering = DatabaseInfraOffering.objects.get(databaseinfra=database.databaseinfra)
    service_offering = infra_offering.offering
    return getattr(service_offering, field)
