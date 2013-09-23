from django import template
from django.contrib.admin.models import LogEntry
from simple_audit.models import Audit

register = template.Library()


class AuditSideBar(template.Node):

  def queryset(self):
    return Audit.objects.all()

@register.tag
def get_audits():
  return AuditSideBar()