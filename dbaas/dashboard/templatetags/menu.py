# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
from django import template

from physical.models import Plan

register = template.Library()

@register.simple_tag
def render_menu():
    plans = Plan.objects.all()
    
    html = """<li class="">
		<a href="javascript:;">
			<i class="fa fa-tasks"></i>&nbsp;Mongodb
			<span class="fa arrow"></span></a>
      <ul>
        <li class="">
          <a href="icon.html">
            <i class="fa fa-angle-right"></i>&nbsp;Dev</a>
        </li>
        <li class="">
          <a href="button.html">
            <i class="fa fa-angle-right"></i>&nbsp;Prod</a>
        </li>
      </ul>
    </li>
    
    <li class="nav-divider"></li>
	"""

    return mark_safe(html)