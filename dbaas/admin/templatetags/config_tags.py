from django import template
from system.models import Configuration

register = template.Library()


@register.assignment_tag
def get_config(conf_name=None):
    if conf_name is None:
        raise Exception("Invalid config name")

    c = Configuration.get_by_name_all_fields(conf_name)
    if not c:
        return None

    return {
        "name": c.name,
        "value": c.value,
        "description": c.description,
        "hash": c.hash
    }


@register.filter
def is_dba(user, name):
    list_validation = Configuration.get_by_name_as_list('list_validation_custom_views')
    is_dba = user.team_set.filter(role__name="role_dba").exists()
    if is_dba or name in list_validation:
        return True
    return False