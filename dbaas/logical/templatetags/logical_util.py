# -*- coding:utf-8 -*-
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def concat(context, left, right, var_name):
    context[var_name] = "{}{}".format(left, right)
    return ''

