from django import template
from simple_audit.models import Audit

register = template.Library()


class AuditSideBar(template.Node):
    def __init__(self, size):
        self.size = size

    def get_qs(self):
        return Audit.objects.all()


@register.tag
def get_audits():
    return AuditSideBar(size=1).get_qs()
