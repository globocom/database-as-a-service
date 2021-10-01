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
