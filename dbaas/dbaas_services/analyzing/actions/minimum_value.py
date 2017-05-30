def database_can_be_resized(database, execution_plan):
    field_value = get_field_value(
        database, execution_plan.field_to_check_value
    )
    return field_value > execution_plan.minimum_value


def get_field_value(database, full_field):
    current_property = database
    for attribute in full_field.split('.'):
        try:
            current_property = getattr(current_property, attribute)
        except AttributeError:
            return -1
        else:
            if callable(current_property):
                current_property = current_property()

    return current_property
