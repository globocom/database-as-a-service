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
            context[self.varname] = Audit.objects.all()[:self.limit]
        else:
            user_id = self.user
            if not user_id.isdigit():
                user_id = context[self.user].id
            context[self.varname] = Audit.objects.filter(audit_request__user_id=user_id)[:int(self.limit)]
        return ''


@register.tag
def get_audit_log(parser, token):
    """
    Populates a template variable with the admin log for the given criteria.

    Usage::

        {% get_audit_log [limit] as [varname] for_user [context_var_containing_user_obj] %}

    Examples::

        {% get_audit_log 10 as admin_log for_user 23 %}
        {% get_audit_log 10 as admin_log for_user user %}
        {% get_audit_log 10 as admin_log %}

    Note that ``context_var_containing_user_obj`` can be a hard-coded integer
    (user ID) or the name of a template context variable containing the user
    object whose ID you want.
    """
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
