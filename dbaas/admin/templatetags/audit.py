from django import template
from simple_audit.models import Audit

register = template.Library()


class AdminAuditNode(template.Node):

    def __init__(self, limit, varname, user):
        self.limit, self.varname, self.user = limit, varname, user

    def __repr__(self):
        return "<GetAdminLog Node>"

    def render(self, context):
        if self.user is None:
            context[self.varname] = Audit.objects.order_by(
                '-date').all()[:self.limit]
        else:
            user_id = self.user
            if not user_id.isdigit():
                user_id = context[self.user].id
            context[self.varname] = Audit.objects.filter(
                audit_request__user_id=user_id).order_by('-date')[:int(self.limit)]
        return ''


@register.tag
def get_audit_log(parser, token):

    tokens = token.contents.split()
    if len(tokens) < 4:
        raise template.TemplateSyntaxError(
            "'get_audit_log' statements require two arguments")
    if not tokens[1].isdigit():
        raise template.TemplateSyntaxError(
            "First argument to 'get_audit_log' must be an integer")
    if tokens[2] != 'as':
        raise template.TemplateSyntaxError(
            "Second argument to 'get_audit_log' must be 'as'")
    if len(tokens) > 4:
        if tokens[4] != 'for_user':
            raise template.TemplateSyntaxError(
                "Fourth argument to 'get_audit_log' must be 'for_user'")
    return AdminAuditNode(limit=tokens[1], varname=tokens[3], user=(len(tokens) > 5 and tokens[5] or None))


@register.filter
def short_description(value, size):
    return ' '.join(value.split()[:size])


@register.filter
def changed_filter(value, size):
    new_field = ''.join(value.split()[-1:])
    return ' '.join(value.split()[:size]).rstrip(':') + ' changed to ' + new_field
