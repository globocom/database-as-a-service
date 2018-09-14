# -*- coding:utf-8 -*-
from django import template

register = template.Library()


# @register.simple_tag(takes_context=True)
# def concat(context, left, right, var_name):
#     context[var_name] = "{}{}".format(left, right)
#     return ''

@register.simple_tag(takes_context=True)
def concat(context, var_name, *args):
    context[var_name] = "{}".format(''.join(str(x) for x in args))
    return ''

